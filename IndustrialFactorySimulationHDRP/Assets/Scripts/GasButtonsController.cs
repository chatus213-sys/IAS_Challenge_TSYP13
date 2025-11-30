using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class GasButtonsController : MonoBehaviour
{
    public enum GasType { None, CO, CO2, PM25, PM10, Temp, Pressure }
    public static GasType SelectedGas { get; private set; } = GasType.None;

    public static System.Action<float, float, float> OnStyleChanged;

    [Header("Heatmaps 1–4 & 6–9 (normal planes)")]
    public List<HeatmapPainter> heatmaps = new List<HeatmapPainter>();

    [Header("Heatmap 5 (MQTT controlled)")]
    public HeatmapPainter mqttHeatmap;

    [Header("Buttons")]
    public Button btn_CO;
    public Button btn_CO2;
    public Button btn_PM25;
    public Button btn_PM10;
    public Button btn_Temp;
    public Button btn_Pressure;

    [Header("Gradients")]
    public Gradient CO_Gradient;
    public Gradient CO2_Gradient;
    public Gradient PM25_Gradient;
    public Gradient PM10_Gradient;
    public Gradient Temp_Gradient;
    public Gradient Pressure_Gradient;

    void Start()
    {
        // normal planes always active
        foreach (var h in heatmaps)
            if (h != null)
                h.allowDrawing = true;

        // heatmap 5 starts invisible
        if (mqttHeatmap != null)
        {
            mqttHeatmap.allowDrawing = false;
            mqttHeatmap.externalStrength = 0f;
        }

        // connect buttons
        btn_CO.onClick.AddListener(() => ApplyGas(GasType.CO));
        btn_CO2.onClick.AddListener(() => ApplyGas(GasType.CO2));
        btn_PM25.onClick.AddListener(() => ApplyGas(GasType.PM25));
        btn_PM10.onClick.AddListener(() => ApplyGas(GasType.PM10));
        btn_Temp.onClick.AddListener(() => ApplyGas(GasType.Temp));
        btn_Pressure.onClick.AddListener(() => ApplyGas(GasType.Pressure));
    }

    void ApplyToNormalHeatmaps(Gradient g, float noise, float speed, float intensity)
    {
        foreach (var h in heatmaps)
        {
            if (h == null) continue;

            h.colorRamp = g;
            h.noiseScale = noise;
            h.animationSpeed = speed;
            h.backgroundIntensity = intensity;
        }

        OnStyleChanged?.Invoke(noise, speed, intensity);
    }

    void ApplyGas(GasType gas)
    {
        // 1) update selected gas for MQTTManager
        SelectedGas = gas;

        // 2) enable heatmap 5
        if (mqttHeatmap != null)
        {
            mqttHeatmap.allowDrawing = true;
            // MQTTManager will set the overlay color
        }

        // 3) tell AlertManager which gas is selected
        

        // 4) apply correct gradient to normal heatmaps
        switch (gas)
        {
            case GasType.CO:
                ApplyToNormalHeatmaps(CO_Gradient, 2f, 0.06f, 0.15f);
                break;
            case GasType.CO2:
                ApplyToNormalHeatmaps(CO2_Gradient, 1.5f, 0.08f, 0.10f);
                break;
            case GasType.PM25:
                ApplyToNormalHeatmaps(PM25_Gradient, 3.5f, 0.01f, 0.18f);
                break;
            case GasType.PM10:
                ApplyToNormalHeatmaps(PM10_Gradient, 1f, 0.01f, 0.50f);
                break;
            case GasType.Temp:
                ApplyToNormalHeatmaps(Temp_Gradient, 2.5f, 0.15f, 0.50f);
                break;
            case GasType.Pressure:
                ApplyToNormalHeatmaps(Pressure_Gradient, 1.5f, 0.05f, 0.30f);
                break;
        }
    }
}
