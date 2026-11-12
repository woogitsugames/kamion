// Candidate only, outside Assets. Not compiled, installed or device-validated.
// Call only for the explicit 0.25 / 0.65 far-industrial payload. Legacy facade
// colours must keep their current contract. Uses existing target-3.0 float ops.
float KamionFarPanelHash(float2 cell)
{
    float2 p = floor(cell);
    p -= floor(p * (1.0 / 1024.0)) * 1024.0;
    // Wrapped integer inputs 0..1023; largest term is 6,410,118, below
    // float32's exact-integer range. Powers of two keep normalization binary.
    float h = p.x * (6.0 * p.x + 1.0) + p.y * 127.0;
    h -= floor(h * (1.0 / 1024.0)) * 1024.0;
    h = h * (6.0 * h + 3.0) + p.y * 17.0;
    return (h - floor(h * (1.0 / 1024.0)) * 1024.0) * (1.0 / 1024.0);
}
