# ADR 0004 — Vehicle physics architecture
Status: Accepted, 2026-11-09
Decision: Pure C# solver (`Game.Vehicle.Physics`, no UnityEngine dependency) computes tire, drivetrain, brake and aero forces; PhysX handles rigid bodies and world collisions; a Unity adapter applies forces at contact points. Fixed step 100 Hz with internal substeps for wheels/drivetrain (count decided by benchmark on Samsung A). The same sources compile in a plain .NET test project (`tools/physics-runner`) so physics can be iterated and tested without the Unity editor.
Consequences: No `transform.position +=` for vehicles; no physics in Update(); zero GC allocations per step.
