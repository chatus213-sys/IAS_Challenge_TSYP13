using System.Text;
using System.Threading.Tasks;
using MQTTnet;
using MQTTnet.Client;
using UnityEngine;

public class MQTTAIAlertManager : MonoBehaviour
{
    private IMqttClient client;

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

            Debug.Log("📥 AI ALERT RAW = " + raw);

            FutureAlertData data = null;

            try
            {
                data = JsonUtility.FromJson<FutureAlertData>(raw);
            }
            catch
            {
                Debug.LogError("❌ Failed to parse AI alert JSON: " + raw);
                return Task.CompletedTask;
            }

            // Send to main thread → show popup
            UnityMainThreadDispatcher.Enqueue(() =>
            {
                Debug.Log("✔ AI ALERT PARSED → level: " + data.level);

                if (FutureAlertUI.Instance != null)
                    FutureAlertUI.Instance.Show(data);
            });

            return Task.CompletedTask;
        };

        await client.ConnectAsync(options);

        Debug.Log("🔥 AI ALERT MQTT CONNECTED");

        await client.SubscribeAsync("");

        Debug.Log("🔥 SUBSCRIBED TO AI TOPIC: ");
    }
}
