using System;
using System.Text;
using System.Threading.Tasks;
using MQTTnet;
using MQTTnet.Client;
using UnityEngine;
using static GasButtonsController;

public class MQTTManager : MonoBehaviour
{
    public static MQTTManager Instance;

    private IMqttClient client;
    public HeatmapPainter mqttHeatmap;

    private float lastMessageTime = -999f;

    void Awake()
    {
        Instance = this;
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

            int end = raw.LastIndexOf('}');
            if (end > 0)
                raw = raw.Substring(0, end + 1);

            Debug.Log("📥 CLEAN RAW MQTT = " + raw);

            MQTTData data = null;
            try
            {
                data = JsonUtility.FromJson<MQTTData>(raw);
            }
            catch
            {
                Debug.LogError("❌ JSON PARSE FAILED: " + raw);
                return Task.CompletedTask;
            }

            UnityMainThreadDispatcher.Enqueue(() =>
            {
                lastMessageTime = Time.time;
                ApplyColor(data);
            });

            return Task.CompletedTask;
        };

        await client.ConnectAsync(options);
        await client.SubscribeAsync("");

        Debug.Log("🔥 MQTT connected.");
    }


    // ===========================
    // FIXED: NO MORE AUTO FADE !!!
    // ===========================
    void Update()
    {
        if (mqttHeatmap == null)
            return;

        // If no gas selected → hide plane 5
        if (SelectedGas == GasType.None)
        {
            mqttHeatmap.allowDrawing = false;
            return;
        }

        // ❌ Removed fade-out logic, color stays forever
    }


    void ApplyColor(MQTTData data)
    {
        if (mqttHeatmap == null)
            return;

        if (SelectedGas == GasType.None)
        {
            mqttHeatmap.allowDrawing = false;
            return;
        }

        mqttHeatmap.allowDrawing = true;

        string colorName = null;

        switch (SelectedGas)
        {
            case GasType.CO:       colorName = data.co;      break;
            case GasType.CO2:      colorName = data.co2;     break;
            case GasType.PM25:     colorName = data.pm2_5;   break;
            case GasType.PM10:     colorName = data.pm10;    break;
            case GasType.Temp:     colorName = data.temp;    break;
            case GasType.Pressure: colorName = data.pressure; break;
        }

        if (string.IsNullOrEmpty(colorName))
        {
            mqttHeatmap.externalStrength = 0f;
            return;
        }

        mqttHeatmap.externalColor = ConvertColor(colorName);
        mqttHeatmap.externalStrength = 0.6f;
    }


    // ===========================
    //  COLOR CONVERSION (UPDATED)
    // ===========================
    Color ConvertColor(string name)
    {
        switch (name.ToLower())
        {
            case "yellow":  return new Color(1f, 0.94f, 0f);
            case "green":   return Color.green;
            case "orange":  return new Color(1f, 0.5f, 0f);
            case "red":     return Color.red;

            // 🔥 NEW COLOR: dark → dark red
            case "dark":    return new Color(0.3f, 0f, 0f);

            case "purple":  return new Color(0.5f, 0f, 0.6f);
        }

        // Allow HEX colors (#FF0000)
        Color parsed;
        if (ColorUtility.TryParseHtmlString(name, out parsed))
            return parsed;

        return Color.clear;
    }
}
