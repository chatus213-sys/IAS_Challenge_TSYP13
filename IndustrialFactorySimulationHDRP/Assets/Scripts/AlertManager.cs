using UnityEngine;
using TMPro;
using UnityEngine.UI;
using System.Collections.Generic;

public class AlertManager : MonoBehaviour
{
    public static AlertManager Instance;

    [Header("UI")]
    public TMP_Text popupText;
    public TMP_Text detailsText;
    public GameObject detailsPanel;
    public Image flashOverlay;

    [Header("Flash Settings")]
    public float flashSpeed = 2f;

    private Color targetFlashColor = Color.clear;

    // === NEW: alert queue ===
    private Queue<MQTTAlertData> alertQueue = new Queue<MQTTAlertData>();

    void Awake()
    {
        Instance = this;

        if (flashOverlay != null)
            flashOverlay.color = Color.clear;

        if (detailsPanel != null)
            detailsPanel.SetActive(false);
    }

    // Called by MQTTAlertManager
    public void OnAlertReceived(MQTTAlertData data)
    {
        if (data == null) return;

        alertQueue.Enqueue(data);

        // If only one alert in queue → show it immediately
        if (alertQueue.Count == 1)
            DisplayNextAlert();
    }

    void DisplayNextAlert()
    {
        if (alertQueue.Count == 0)
        {
            CloseAlert();
            return;
        }

        // Dequeue next alert
        MQTTAlertData data = alertQueue.Peek();

        // Flash overlay according to level
        targetFlashColor = LevelToColor(data.level);

        // Multi-gas popup title (show all gas names in queue)
        popupText.text = BuildPopupTitle();

        // Multi-details (all alerts in queue)
        detailsText.text = BuildDetailsText();

        // Force details panel visible
        detailsPanel.SetActive(true);
    }

    string BuildPopupTitle()
    {
        string result = "ALERT: ";

        foreach (var a in alertQueue)
            result += a.gas.ToUpper() + "  ";

        return result;
    }

    string BuildDetailsText()
    {
        string text = "";

        foreach (var a in alertQueue)
        {
            text +=
                $"Gas: {a.gas}\n" +
                $"Level: {a.level}\n" +
                $"Value: {a.value}\n" +
                $"Time: {a.timestamp}\n" +
                "-----------------------\n";
        }

        return text;
    }

    // Close button
    public void CloseAlert()
    {
        if (alertQueue.Count > 0)
        {
            // Remove current alert
            alertQueue.Dequeue();

            // Show next one OR hide everything
            if (alertQueue.Count > 0)
                DisplayNextAlert();
            else
            {
                // no more alerts
                targetFlashColor = Color.clear;
                detailsPanel.SetActive(false);
                popupText.text = "";
            }
        }
    }

    void Update()
    {
        if (flashOverlay != null)
        {
            flashOverlay.color = Color.Lerp(
                flashOverlay.color,
                targetFlashColor,
                Time.deltaTime * flashSpeed
            );
        }
    }

    Color LevelToColor(string level)
    {
        switch (level.ToLower())
        {
            case "normal": return new Color(1f, 1f, 0f, 0.2f);
            case "warning": return new Color(1f, 0.6f, 0f, 0.3f);
            case "high": return new Color(1f, 0f, 0f, 0.35f);
            case "critical": return new Color(0f, 1f, 0f, 0.35f);
        }
        return new Color(1f, 1f, 0f, 0.2f);
    }
}
