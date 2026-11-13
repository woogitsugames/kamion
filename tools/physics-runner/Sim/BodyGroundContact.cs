using System;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Axis-aligned collider box in the body (vehicle) frame [m].</summary>
    public struct ColliderBox
    {
        public string Name;
        public Vec3 Center, Size;
        public ColliderBox(string name, Vec3 center, Vec3 size) { Name = name; Center = center; Size = size; }
    }

    /// <summary>
    /// Chassis-to-ground contact of the .NET runner (ADR 0158, compliant since ADR 0165 / owner decision D58).
    /// In Unity the tractor and trailer are PhysX rigid bodies with BoxColliders (GrayboxTractorBuilder "Colliders":
    /// Frame, Cab, Bumper; GrayboxTrailerBuilder: Body, Beams, RearUnderrun), so a vehicle that has rolled over lands on
    /// its cab/body and slides. Without such a contact the runner's stand-in body fell through the road (F2).
    ///
    /// Model: the 8 corners of every collider box are tested against the ground with a vertical ray (exact for a box on a
    /// plane, where the contact set is always a subset of the corners). Each corner below the surface carries a
    /// unilateral linear spring-damper along the ground normal, F_n = max(0, k pen + c pen_rate) (ADR 0165): bumper
    /// covers, brackets, underrun bars and body panels crush and scrape on the road instead of the rigid, infinitely
    /// stiff contact that gave a single-step velocity jump on the 27 cm kerb (bumper corner 0.35 m above the road).
    /// The spring-damper is integrated implicitly (soft constraint, E. Catto "Soft Constraints", GDC 2011; Box2D v3
    /// soft step): the force is evaluated at the end of the step, F = k pen_end + c pen_rate_end, solved together with
    /// Coulomb friction (circular cone on the accumulated tangential impulse) by projected Gauss-Seidel on the velocity
    /// the body will have at the end of the step given the solver forces. That keeps it stable for any k, c, dt, and a
    /// corner approaching the surface feels the spring only for the part of the step it spends below it (no rigid
    /// speculative stop). The result is an extra force/torque (impulse / dt) for <see cref="RigidBody6Dof.Integrate"/>.
    /// No allocations per step (fixed arrays sized from the collider set).
    /// </summary>
    public sealed class BodyGroundContact
    {
        /// <summary>
        /// Body-on-road Coulomb friction. WORKING_VALUE = 0.6: parity with Unity's default PhysicsMaterial
        /// (dynamic = static = 0.6, bounciness 0, combine Average), which is what the graybox colliders and a ground
        /// collider without a material use. Physical value for a steel/painted body sliding on asphalt: UNVERIFIED.
        /// </summary>
        public double Friction = 0.6;
        /// <summary>
        /// Contact natural frequency [Hz] and damping ratio [-] per collider corner (ADR 0165) — WORKING_VALUE, see
        /// <see cref="DefaultHertz"/>. Each corner spring is scaled by that corner's effective mass along the normal,
        /// k = m_eff (2 pi f)^2, c = 2 zeta m_eff (2 pi f) (the "soft contact" parameterisation of Box2D v3:
        /// b2_contactHertz / contactDampingRatio; E. Catto, Solver2D, 2024). A fixed k in N/m cannot serve both the
        /// light bumper corner hitting the road (needs soft: jerk limit) and a 30 t trailer lying on two corners
        /// (needs stiff: no sinking); a fixed frequency gives every corner the same static sink ~ a/(2 pi f)^2.
        /// </summary>
        public double Hertz = DefaultHertz, DampingRatio = DefaultDampingRatio;
        /// <summary>
        /// Defaults for new instances — WORKING_VALUE (ADR 0165; runner CLI --body-hz / --body-zeta for a sweep, table
        /// in the ADR). No measured crush stiffness exists for this fictional truck. Bounds: the 27 cm kerb bumper
        /// strike (corner ~3.5 m/s into the road, m_eff ~1.5 t) must stay under the jerk limit max_dv_step 0.35 m/s
        /// (D58), which caps f; the lying laden trailer (corner load ~2 g of its m_eff) must not visibly sink, which
        /// floors f. zeta: crushing plastic covers, brackets and panels do not bounce (PhysX default restitution 0).
        /// </summary>
        public static double DefaultHertz = 4.0, DefaultDampingRatio = 1.0;
        /// <summary>PGS iterations — WORKING_VALUE (PhysX default solverIterations is 6; 10 here, the system is tiny).</summary>
        public int Iterations = 10;
        /// <summary>Ray start above the corner [m] (= deepest penetration that is still resolved) and reach below it [m].</summary>
        public double CastAbove = 0.5, SpeculativeReach = 0.1;

        readonly Vec3[] _cornersLocal;
        readonly Vec3[] _r, _n, _t1, _t2;
        readonly double[] _rhs, _soft, _sc, _mn, _mt1, _mt2, _jn, _jt1, _jt2;
        int _count;

        /// <summary>Extra force / torque about the CoM (world) for this step = contact impulse / dt. Valid after <see cref="Solve"/>.</summary>
        public Vec3 Force, Torque;
        /// <summary>Corners in (or near) contact this step.</summary>
        public int ContactCount => _count;
        /// <summary>Corners with a non-zero normal impulse this step.</summary>
        public int ActiveContacts { get; private set; }
        /// <summary>Deepest corner penetration found at the start of this step [m] (0 when none).</summary>
        public double MaxPenetration { get; private set; }
        /// <summary>Index of the deepest corner this step (8 per collider box, in collider order); -1 when none is below the road.</summary>
        public int DeepestCorner { get; private set; } = -1;
        /// <summary>Total normal impulse this step [N s].</summary>
        public double NormalImpulse { get; private set; }
        /// <summary>Elastic energy stored in the corner springs at the start of this step, sum 0.5 k pen^2 [J].</summary>
        public double SpringEnergy { get; private set; }

        public BodyGroundContact(ColliderBox[] boxes)
        {
            _cornersLocal = new Vec3[boxes.Length * 8];
            int k = 0;
            foreach (var b in boxes)
                for (int sx = -1; sx <= 1; sx += 2)
                    for (int sy = -1; sy <= 1; sy += 2)
                        for (int sz = -1; sz <= 1; sz += 2)
                            _cornersLocal[k++] = b.Center + new Vec3(sx * 0.5 * b.Size.x, sy * 0.5 * b.Size.y, sz * 0.5 * b.Size.z);
            int n = _cornersLocal.Length;
            _r = new Vec3[n]; _n = new Vec3[n]; _t1 = new Vec3[n]; _t2 = new Vec3[n];
            _rhs = new double[n]; _soft = new double[n]; _sc = new double[n]; _mn = new double[n]; _mt1 = new double[n]; _mt2 = new double[n];
            _jn = new double[n]; _jt1 = new double[n]; _jt2 = new double[n];
        }

        public int CornerCount => _cornersLocal.Length;
        public Vec3 CornerLocal(int i) => _cornersLocal[i];

        /// <summary>
        /// Computes the contact force/torque for one step of <paramref name="b"/> under the solver force
        /// <paramref name="force"/> and torque <paramref name="torque"/> (gravity is added by the body).
        /// Call right before <c>b.Integrate(dt, force + Force, torque + Torque)</c>.
        /// </summary>
        public void Solve(RigidBody6Dof b, Vec3 force, Vec3 torque, double dt, IGroundQuery ground)
        {
            Force = Vec3.Zero; Torque = Vec3.Zero; _count = 0; ActiveContacts = 0; MaxPenetration = 0; DeepestCorner = -1; NormalImpulse = 0; SpringEnergy = 0;
            Quat q = b.Rotation;
            Vec3 com = b.CenterOfMassWorld;
            Vec3 down = new Vec3(0, -1, 0);
            // Implicit spring-damper per corner: normal impulse j = dt (k pen_end + c rate_end), pen_end = pen + dt rate_end,
            // rate_end = -vn_end  =>  j = dt k pen - dt (k dt + c) vn_end.  PGS form on the accumulated j:
            //   dj = (pen k/(k dt + c) - vn - sc j) / (1/m_eff + sc),  sc = 1 / (dt (k dt + c)).
            double omega = 2 * Math.PI * Hertz;
            for (int i = 0; i < _cornersLocal.Length; i++)
            {
                Vec3 p = b.Position + q * _cornersLocal[i];
                if (!ground.Raycast(p + Vec3.Up * CastAbove, down, CastAbove + SpeculativeReach, out GroundHit hit)) continue;
                Vec3 nrm = hit.Normal;
                double pen = Vec3.Dot(hit.Point - p, nrm); // > 0: corner below the surface
                if (pen < -SpeculativeReach) continue;
                int c = _count++;
                _r[c] = p - com; _n[c] = nrm;
                Vec3 t1 = Math.Abs(nrm.x) < 0.9 ? Vec3.Cross(nrm, Vec3.Right).Normalized : Vec3.Cross(nrm, Vec3.Forward).Normalized;
                _t1[c] = t1; _t2[c] = Vec3.Cross(nrm, t1);
                // pen >= 0: implicit spring-damper target.  pen < 0 (above): free approach up to the gap this step
                // (speculative, no tunnelling); only the predicted part below the surface feels the soft contact, so
                // the damper never pushes a corner that is still above the road.
                _mn[c] = EffMass(b, q, _r[c], nrm); _mt1[c] = EffMass(b, q, _r[c], t1); _mt2[c] = EffMass(b, q, _r[c], _t2[c]);
                double k = _mn[c] * omega * omega, kc = k * dt + 2 * DampingRatio * _mn[c] * omega;
                _rhs[c] = pen >= 0 ? pen * k / kc : pen / dt;
                _sc[c] = 1.0 / (dt * kc);
                _soft[c] = 1.0 / (1.0 / _mn[c] + _sc[c]);
                _jn[c] = 0; _jt1[c] = 0; _jt2[c] = 0;
                if (pen > MaxPenetration) { MaxPenetration = pen; DeepestCorner = i; }
                if (pen > 0) SpringEnergy += 0.5 * k * pen * pen;
            }
            if (_count == 0) return;

            // Velocity at the end of the step without contact (same update as RigidBody6Dof.Integrate).
            Vec3 v = b.Velocity + (force / b.Mass + b.Gravity) * dt;
            Vec3 w = b.PredictAngularVelocity(torque, dt);

            Vec3 jLin = Vec3.Zero, jAng = Vec3.Zero;
            for (int it = 0; it < Iterations; it++)
            {
                for (int c = 0; c < _count; c++)
                {
                    Vec3 r = _r[c];
                    // normal: implicit spring-damper, unilateral (j >= 0: the road only pushes)
                    double vn = Vec3.Dot(v + Vec3.Cross(w, r), _n[c]);
                    double dj = _soft[c] * (_rhs[c] - vn - _sc[c] * _jn[c]);
                    double jOld = _jn[c];
                    _jn[c] = Math.Max(0, jOld + dj);
                    dj = _jn[c] - jOld;
                    if (dj != 0) Apply(b, q, r, _n[c] * dj, ref v, ref w, ref jLin, ref jAng);
                    // friction (circular Coulomb cone on the accumulated tangential impulse)
                    Vec3 vp = v + Vec3.Cross(w, r);
                    double a1 = _jt1[c] - _mt1[c] * Vec3.Dot(vp, _t1[c]);
                    double a2 = _jt2[c] - _mt2[c] * Vec3.Dot(vp, _t2[c]);
                    double lim = Friction * _jn[c];
                    double mag = Math.Sqrt(a1 * a1 + a2 * a2);
                    if (mag > lim) { double s = mag > 1e-12 ? lim / mag : 0; a1 *= s; a2 *= s; }
                    double d1 = a1 - _jt1[c], d2 = a2 - _jt2[c];
                    _jt1[c] = a1; _jt2[c] = a2;
                    if (d1 != 0 || d2 != 0) Apply(b, q, r, _t1[c] * d1 + _t2[c] * d2, ref v, ref w, ref jLin, ref jAng);
                }
            }
            int active = 0; double jnSum = 0;
            for (int c = 0; c < _count; c++) if (_jn[c] > 0) { active++; jnSum += _jn[c]; }
            ActiveContacts = active; NormalImpulse = jnSum;
            Force = jLin / dt;
            Torque = jAng / dt;
            if (Dbg) for (int c = 0; c < _count; c++) if (_jn[c] > 0) Console.WriteLine($"DBG body m {b.Mass:F0} p {com + _r[c]} vcom {b.Velocity} w {b.AngularVelocity} rhs {_rhs[c]:F3} jn {_jn[c]:F0} jt {_jt1[c]:F0},{_jt2[c]:F0} meff {_mn[c]:F0}");
        }
        public static bool Dbg = Environment.GetEnvironmentVariable("BODYDBG") == "1";

        static Vec3 InvInertiaWorld(RigidBody6Dof b, Quat q, Vec3 x) => q * (b.InvInertiaLocal * q.InverseRotate(x));

        static double EffMass(RigidBody6Dof b, Quat q, Vec3 r, Vec3 d)
        {
            Vec3 rd = Vec3.Cross(r, d);
            double k = 1.0 / b.Mass + Vec3.Dot(rd, InvInertiaWorld(b, q, rd));
            return 1.0 / k;
        }

        static void Apply(RigidBody6Dof b, Quat q, Vec3 r, Vec3 j, ref Vec3 v, ref Vec3 w, ref Vec3 jLin, ref Vec3 jAng)
        {
            Vec3 l = Vec3.Cross(r, j);
            v += j / b.Mass;
            w += InvInertiaWorld(b, q, l);
            jLin += j; jAng += l;
        }

        // ---------------- collider sets (mirror of the Unity graybox builders) ----------------

        /// <summary>
        /// Tractor colliders as built by GrayboxTractorBuilder.Build (game/Assets/_Project/Vehicle/Runtime, "colliders"
        /// block) with TractorDimensions defaults; the wheelbase is taken from the definition (front axle positionZ).
        /// Values are DERIVED from those files — keep in sync (ADR 0158, Open: single data source).
        /// </summary>
        public static ColliderBox[] TractorColliders(VehicleDefinition def)
        {
            double wheelbase = 0;
            foreach (var a in def.axles) wheelbase = Math.Max(wheelbase, a.positionZ);
            const double frontOverhang = 1.45, rearOverhang = 0.80, cabWidth = 2.49, overallHeight = 3.75;
            const double cabBackBehindFrontAxle = 0.95, cabBodyBottom = 1.15, frameWidthOuter = 0.85, frameTopHeight = 0.97;
            double frontFace = wheelbase + frontOverhang, rearEnd = -rearOverhang, cabRear = wheelbase - cabBackBehindFrontAxle;
            double frameLen = frontFace - rearEnd;
            double cabLen = frontFace - 0.05 - cabRear, cabH = overallHeight - cabBodyBottom;
            return new[]
            {
                new ColliderBox("Frame", new Vec3(0, frameTopHeight - 0.11, rearEnd + frameLen * 0.5), new Vec3(frameWidthOuter, 0.22, frameLen)),
                new ColliderBox("Cab", new Vec3(0, cabBodyBottom + cabH * 0.5, cabRear + cabLen * 0.5), new Vec3(cabWidth, cabH, cabLen)),
                new ColliderBox("Bumper", new Vec3(0, 0.60, frontFace - 0.10), new Vec3(cabWidth - 0.04, 0.50, 0.20)),
            };
        }

        /// <summary>
        /// Trailer colliders as built by GrayboxTrailerBuilder.Build with TrailerDimensions defaults (13.6 x 2.55 x 4.0 m)
        /// and the definition's cargo bay / landing gear positions. DERIVED — keep in sync (ADR 0158).
        /// </summary>
        public static ColliderBox[] TrailerColliders(TrailerDefinition def)
        {
            const double length = 13.6, width = 2.55, height = 4.0, frontWall = 0.05, plateBottom = 1.15, beamBottom = 0.92;
            const double rupdBottom = 0.40, rupdTop = 0.55;
            double front = def.cargoBay.frontZ + frontWall, rear = front - length;
            double floorBottom = def.cargoBay.floorHeight - 0.10;
            double lgZ = def.landingGear.positionZ;
            return new[]
            {
                new ColliderBox("Body", new Vec3(0, (plateBottom + 0.07 + height) * 0.5, (front + rear) * 0.5),
                    new Vec3(width, height - plateBottom - 0.07, length)),
                new ColliderBox("Beams", new Vec3(0, (beamBottom + floorBottom) * 0.5, (lgZ - 0.4 + rear + 0.1) * 0.5),
                    new Vec3(1.2, floorBottom - beamBottom, lgZ - 0.4 - rear - 0.1)),
                new ColliderBox("RearUnderrun", new Vec3(0, (rupdBottom + rupdTop) * 0.5, rear + 0.25),
                    new Vec3(2.35, rupdTop - rupdBottom, 0.12)),
            };
        }
    }
}
