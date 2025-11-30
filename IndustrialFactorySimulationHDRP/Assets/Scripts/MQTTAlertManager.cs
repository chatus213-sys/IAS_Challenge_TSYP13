using System.Text;
using System.Threading.Tasks;
using MQTTnet;
using MQTTnet.Client;
using UnityEngine;

public class MQTTAlertManager : MonoBehaviour
{
    private IMqttClient client;

    [System.Serializable]
    private class AlertListWrapper
    {
        public MQTTAlertData[] items;
    }

    async void Start()
    {
        var factory = new MqttFactory();
        client = factory.CreateMqttClient();

        var options = new MqttClientOptionsBuilder()
            .WithTcpServer("broker.hivemq.com", 1883)
            .WithCleanSession()
            .Build();

        client.ApplicationMessageReceivedAsync += e =>
        {
            string raw = Encoding.UTF8.GetString(e.ApplicationMessage.PayloadSegment);

            Debug.Log("📡 ALERT MESSAGE ARRIVED");
            Debug.Log("📡 TOPIC  = " + e.ApplicationMessage.Topic);
            Debug.Log("📥 RAW    = " + raw);

            if (string.IsNullOrWhiteSpace(raw))
            {
                Debug.LogError("❌ Alert payload empty");
                return Task.CompletedTask;
            }

            raw = raw.Trim();

            // ---------- 1) EXTRACT JSON PART ----------
            // We support 2 cases:
            //   - a list:   [..., ...]
            //   - a single: {...}

            string jsonPart = null;

            int firstBracket = raw.IndexOf('[');
            int lastBracket  = raw.LastIndexOf(']');
            int firstBrace   = raw.IndexOf('{');
            int lastBrace    = raw.LastIndexOf('}');

            if (firstBracket >= 0 && lastBracket > firstBracket)
            {
                // There is an array inside some text → take only [ ... ]
                jsonPart = raw.Substring(firstBracket, lastBracket - firstBracket + 1);
                Debug.Log("🔍 Detected JSON LIST: " + jsonPart);

                string wrapped = "{\"items\":" + jsonPart + "}";
                try
                {
                    AlertListWrapper container = JsonUtility.FromJson<AlertListWrapper>(wrapped);
                    if (container?.items != null)
                    {
                        foreach (var alert in container.items)
                        {
                            UnityMainThreadDispatcher.Enqueue(() =>
                            {
                                Debug.Log("✔ Parsed alert for gas = " + alert.gas);
                                AlertManager.Instance?.OnAlertReceived(alert);
                            });
                        }
                    }
                    else
                    {
                        Debug.LogError("❌ Parsed list but got null items");
                    }
                }
                catch (System.Exception ex)
                {
                    Debug.LogError("❌ Failed to parse alert list: " + ex.Message);
                }

                return Task.CompletedTask;
            }
            else if (firstBrace >= 0 && lastBrace > firstBrace)
            {
                // Single JSON object {...} inside some text
                jsonPart = raw.Substring(firstBrace, lastBrace - firstBrace + 1);
                Debug.Log("🔍 Detected SINGLE JSON: " + jsonPart);

                try
                {
                    MQTTAlertData single = JsonUtility.FromJson<MQTTAlertData>(jsonPart);

                    UnityMainThreadDispatcher.Enqueue(() =>
                    {
                        Debug.Log("✔ Parsed single alert for gas = " + single.gas);
                        AlertManager.Instance?.OnAlertReceived(single);
                    });
                }
                catch (System.Exception ex)
                {
                    Debug.LogError("❌ Failed to parse single alert: " + ex.Message);
                }

                return Task.CompletedTask;
            }
            else
            {
                Debug.LogError("❌ No JSON [ ] or { } found in alert payload");
                return Task.CompletedTask;
            }
        };

        await client.ConnectAsync(options);
        Debug.Log("🔥 ALERT MQTT CONNECTED");

        // VERY IMPORTANT: this MUST match MQTT_UNITY_ALERT_TOPIC
        await client.SubscribeAsync("");
        Debug.Log("🔥 SUBSCRIBED TO: ");
    }
}
