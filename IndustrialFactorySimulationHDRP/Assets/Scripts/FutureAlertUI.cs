using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class FutureAlertUI : MonoBehaviour
{
    public static FutureAlertUI Instance;

    [Header("UI Root (overlay)")]
    public GameObject root;

    [Header("Dark background")]
    public Image darkener;

    [Header("Texts")]
    public TMP_Text titleText;
    public TMP_Text bodyText;

    [Header("Buttons")]
    public Button okButton;

    private float previousTimeScale = 1f;

    void Awake()
    {
        Instance = this;

        if (root != null)
            root.SetActive(false);

        if (darkener != null)
            darkener.gameObject.SetActive(false);
    }

    // Called by MQTTAIAlertManager
    public void Show(FutureAlertData data)
    {
        if (root == null) return;

        // Block the game-like Unity error popup
        previousTimeScale = Time.timeScale;
        Time.timeScale = 0f;

        root.SetActive(true);
        if (darkener != null)
            darkener.gameObject.SetActive(true);

        // Title
        if (titleText != null)
            titleText.text = "AI FUTURE ALERT";

        // Body
        if (bodyText != null)
        {
            bodyText.text =
                $"Source: {data.source}\n" +
                $"Predicted PPM: {data.predicted_ppm}\n" +
                $"Level: {data.level}\n" +
                $"Timestamp: {data.timestamp}";

        }
    }

    public void OnOkClicked()
    {
        if (root != null)
            root.SetActive(false);

        if (darkener != null)
            darkener.gameObject.SetActive(false);

        // Resume game
        Time.timeScale = previousTimeScale;
    }
}
