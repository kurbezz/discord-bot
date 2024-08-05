use anyhow::bail;
use anyhow::Result;
use futures::Future;
use futures::Sink;
use futures::StreamExt;

use serde::Deserialize;

use futures::Stream;

use std::pin::Pin;
use std::task::Context;
use std::task::Poll;

use super::auth;
use super::helix;

#[derive(Debug, Deserialize)]
pub struct MessageMetadata {
    pub message_id: String,
    pub message_timestamp: String,
    pub message_type: String,
    pub subscription_type: Option<String>,
    pub subscription_version: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Message {
    pub metadata: MessageMetadata,
    pub payload: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct SessionWelcomeSession {
    pub id: String,
    pub connected_at: String,
    pub status: String,
    pub reconnect_url: Option<String>,
    pub keepalive_timeout_seconds: i64,
}

#[derive(Debug, Deserialize)]
pub struct SessionWelcome {
    pub session: SessionWelcomeSession,
}

#[derive(Debug, Deserialize)]
pub struct Notification {
    pub subscription: serde_json::Value,
    pub event: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct ChannelUpdate {
    pub broadcaster_user_id: String,
    pub broadcaster_user_login: String,
    pub broadcaster_user_name: String,
    pub title: String,
    pub language: String,
    pub category_id: String,
    pub category_name: String,
    pub content_classification_labels: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct CustomRewardRedemptionAddReward {
    pub id: String,
}

#[derive(Debug, Deserialize)]
pub struct CustomRewardRedemptionAdd {
    pub id: String,
    pub user_login: String,
    pub user_input: String,
    pub reward: CustomRewardRedemptionAddReward,
}

#[derive(Debug, Deserialize)]
pub struct StreamOnline {
    pub id: String,
    pub broadcaster_user_id: String,
    pub broadcaster_user_login: String,
    pub broadcaster_user_name: String,
    pub r#type: String,
    pub started_at: String,
}

#[derive(Debug, Deserialize)]
pub struct StreamOffline {
    pub broadcaster_user_id: String,
    pub broadcaster_user_login: String,
    pub broadcaster_user_name: String,
}

#[derive(Debug, Deserialize)]
pub enum NotificationType {
    ChannelUpdate(ChannelUpdate),
    CustomRewardRedemptionAdd(CustomRewardRedemptionAdd),
    StreamOnline(StreamOnline),
    StreamOffline(StreamOffline),
}

pub struct Client {
    inner_stream: Pin<
        Box<
            tokio_tungstenite::WebSocketStream<
                tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>,
            >,
        >,
    >,
    ping_sleep: Pin<Box<tokio::time::Sleep>>,
}

impl Stream for Client {
    type Item = NotificationType;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        let this = self.get_mut();
        let mut inner_stream = this.inner_stream.as_mut();

        match this.ping_sleep.as_mut().poll(cx) {
            Poll::Pending => {}
            Poll::Ready(..) => {
                this.ping_sleep
                    .as_mut()
                    .reset(tokio::time::Instant::now() + tokio::time::Duration::from_secs(30));

                match inner_stream.as_mut().start_send(
                    tokio_tungstenite::tungstenite::protocol::Message::Ping(vec![]),
                ) {
                    Err(..) => return Poll::Ready(None),
                    _ => {}
                };
            }
        };

        loop {
            match inner_stream.as_mut().poll_next(cx) {
                Poll::Pending => return Poll::Pending,
                Poll::Ready(v) => match v {
                    Some(Ok(tokio_tungstenite::tungstenite::protocol::Message::Ping(..))) => {
                        match inner_stream.as_mut().start_send(
                            tokio_tungstenite::tungstenite::protocol::Message::Pong(vec![]),
                        ) {
                            Ok(()) => continue,
                            Err(..) => break,
                        };
                    }
                    Some(Ok(tokio_tungstenite::tungstenite::protocol::Message::Text(text))) => {
                        let message: Message = match serde_json::from_str(&text) {
                            Ok(v) => v,
                            Err(..) => break,
                        };

                        match message.metadata.message_type.as_str() {
                            "notification" => {
                                let subtype = match &message.metadata.subscription_type {
                                    Some(v) => v,
                                    None => break,
                                };

                                let notification: Notification =
                                    match serde_json::from_value(message.payload.clone()) {
                                        Ok(v) => v,
                                        Err(..) => break,
                                    };

                                match subtype.as_str() {
                                    "channel.update" => {
                                        let event: ChannelUpdate =
                                            match serde_json::from_value(notification.event) {
                                                Ok(v) => v,
                                                Err(..) => break,
                                            };

                                        return Poll::Ready(Some(NotificationType::ChannelUpdate(
                                            event,
                                        )));
                                    }
                                    "channel.channel_points_custom_reward_redemption.add" => {
                                        let event: CustomRewardRedemptionAdd =
                                            match serde_json::from_value(notification.event) {
                                                Ok(v) => v,
                                                Err(..) => break,
                                            };

                                        return Poll::Ready(Some(
                                            NotificationType::CustomRewardRedemptionAdd(event),
                                        ));
                                    }
                                    "stream.online" => {
                                        let event: StreamOnline =
                                            match serde_json::from_value(notification.event) {
                                                Ok(v) => v,
                                                Err(..) => break,
                                            };

                                        return Poll::Ready(Some(NotificationType::StreamOnline(
                                            event,
                                        )));
                                    }
                                    "stream.offline" => {
                                        let event: StreamOffline =
                                            match serde_json::from_value(notification.event) {
                                                Ok(v) => v,
                                                Err(..) => break,
                                            };

                                        return Poll::Ready(Some(NotificationType::StreamOffline(
                                            event,
                                        )));
                                    }
                                    _ => return Poll::Pending,
                                }
                            }
                            _ => continue,
                        }
                    }
                    Some(..) => continue,
                    None => break,
                },
            }
        }

        Poll::Ready(None)
    }
}

impl<T: auth::TokenStorage> helix::Client<T> {
    pub async fn connect_eventsub(&mut self, topics: Vec<(String, String)>, broadcaster_id: String) -> Result<Client> {
        let (mut ws_stream, _) =
            match tokio_tungstenite::connect_async("wss://eventsub.wss.twitch.tv/ws").await {
                Ok(v) => v,
                Err(e) => return Err(e.into()),
            };

        let welcome = loop {
            let msg = ws_stream.next().await;
            match msg {
                Some(Ok(tokio_tungstenite::tungstenite::protocol::Message::Text(text))) => {
                    let message: Message = match serde_json::from_str(&text) {
                        Ok(v) => v,
                        Err(e) => return Err(e.into()),
                    };

                    if message.metadata.message_type.as_str() != "session_welcome" {
                        bail!("No session welcome");
                    }

                    let welcome: SessionWelcome =
                        match serde_json::from_value(message.payload.clone()) {
                            Ok(v) => v,
                            Err(e) => return Err(e.into()),
                        };

                    break welcome;
                }
                Some(Err(e)) => return Err(e.into()),
                Some(..) => {}
                None => bail!("WebSocket dropped"),
            }
        };

        for (subtype, version) in topics.into_iter() {
            match self
                .create_eventsub_subscription(&helix::EventSubCreate {
                    r#type: subtype,
                    version: version,
                    condition: helix::EventSubCondition {
                        broadcaster_id: Some(broadcaster_id.clone()),
                        broadcaster_user_id: Some(broadcaster_id.clone()),
                        moderator_user_id: Some(broadcaster_id.clone()),
                        user_id: Some(broadcaster_id.clone()),
                        ..Default::default()
                    },
                    transport: helix::EventSubTransport {
                        method: "websocket".to_string(),
                        session_id: Some(welcome.session.id.clone()),
                        ..Default::default()
                    },
                })
                .await
            {
                Ok(..) => {}
                Err(err) => {
                    bail!("create_eventsub_subscription failed {:?}", err);
                }
            };
        }

        Ok(Client {
            inner_stream: Pin::new(Box::new(ws_stream)),
            ping_sleep: Box::pin(tokio::time::sleep(tokio::time::Duration::from_secs(30))),
        })
    }
}
