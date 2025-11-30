using UnityEngine;

public class HeatmapPainter : MonoBehaviour
{
    [Header("Runtime Values")]
    public Gradient colorRamp;               // base gradient (yellow for plane 5)
    public float noiseScale = 2f;
    public float animationSpeed = 0.3f;
    public float backgroundIntensity = 0.15f;

    [Header("External MQTT overlay")]
    public Color externalColor = Color.clear; // overlay color from MQTT
    public float externalStrength = 0.0f;     // 0 = no overlay, 1 = full overlay

    [Header("State")]
    public bool allowDrawing = true;         // plane 5: false when no gas selected

    private Texture2D tex;
    private Color[] pixels;
    private Renderer rend;

    private int seedOffset;
    private int w = 512;
    private int h = 512;

    void Start()
    {
        rend = GetComponent<Renderer>();
        // make unique material instance
        rend.material = new Material(rend.material);

        tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        tex.wrapMode = TextureWrapMode.Clamp;

        pixels = new Color[w * h];
        seedOffset = Random.Range(0, 99999);

        rend.material.SetTexture("_BaseMap", tex);
    }
void Update()
{
    if (tex == null || pixels == null)
        return;

    // 🔴 If not allowed (no gas selected) → clear texture
    if (!allowDrawing)
    {
        for (int index = 0; index < pixels.Length; index++)
            pixels[index] = Color.clear;

        tex.SetPixels(pixels);
        tex.Apply();
        return;
    }

    float t = Time.time * animationSpeed + seedOffset;

    int index2 = 0;

    for (int y = 0; y < h; y++)
    {
        float ny = (float)y / h * noiseScale;

        for (int x = 0; x < w; x++, index2++)
        {
            float nx = (float)x / w * noiseScale;

            float v = Mathf.PerlinNoise(nx + t, ny + t);
            v = Mathf.Lerp(backgroundIntensity, 1f, v);

            // Base yellow gradient
            Color c = colorRamp.Evaluate(v);

            // MQTT noisy overlay
            if (externalStrength > 0f && externalColor.a > 0f)
            {
                float overlayNoise = Mathf.PerlinNoise((nx * 1.5f) + t * 1.3f,
                                                       (ny * 1.5f) - t * 1.1f);

                float mask = overlayNoise * externalStrength;

                c = Color.Lerp(c, externalColor, mask);
            }

            pixels[index2] = c;
        }
    }

    tex.SetPixels(pixels);
    tex.Apply();
}

}
