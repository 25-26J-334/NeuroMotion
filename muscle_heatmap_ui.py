import streamlit as st
import streamlit.components.v1 as components
import json
from database import Database

def render_3d_heatmap(user_id, exercise_data=None):
    """
    Renders a 3D Humanoid Heatmap using Three.js
    user_id: ID of the user to fetch stats for
    exercise_data: Optional dict with manual overrides (e.g. for a single session)
    """
    
    # 1. Fetch Data from DB if not provided
    if not exercise_data:
        db = Database()
        # Get recent sessions to calculate muscle load
        recent_sessions = db.get_recent_sessions(user_id, limit=5)
        
        # Aggregate stats
        stats = {
            'jumps': 0,
            'squats': 0,
            'pushups': 0,
            'bad_moves': 0,
            'valgus_count': 0,
            'lean_count': 0,
            'toe_count': 0
        }
        
        if recent_sessions:
            for s in recent_sessions:
                stats['jumps'] += s.get('total_jumps', 0) or 0
                stats['squats'] += s.get('total_squats', 0) or 0
                stats['pushups'] += s.get('total_pushups', 0) or 0
                stats['bad_moves'] += s.get('total_bad_moves', 0) or 0
        
        # Mocking some granular stress for demo if bad_moves exist
        if stats['bad_moves'] > 0:
            stats['valgus_count'] = stats['bad_moves'] // 2
            stats['lean_count'] = stats['bad_moves'] // 3
            stats['toe_count'] = max(0, stats['bad_moves'] - (stats['valgus_count'] + stats['lean_count']))
            
        exercise_data = stats

    # 2. Muscle Intensity Logic (Normalized 0-1)
    # Target Muscles
    quads = min(1.0, (exercise_data['squats'] * 0.05 + exercise_data['jumps'] * 0.03))
    glutes = min(1.0, (exercise_data['squats'] * 0.04 + exercise_data['jumps'] * 0.02))
    chest = min(1.0, (exercise_data['pushups'] * 0.05))
    triceps = min(1.0, (exercise_data['pushups'] * 0.03))
    calves = min(1.0, (exercise_data['jumps'] * 0.06))
    core = min(1.0, (exercise_data['pushups'] * 0.02 + exercise_data['squats'] * 0.01 + exercise_data['jumps'] * 0.01))
    
    # Stress (Red)
    knee_stress = min(1.0, (exercise_data.get('valgus_count', 0) * 0.2 + exercise_data.get('toe_count', 0) * 0.15))
    back_stress = min(1.0, (exercise_data.get('lean_count', 0) * 0.3))
    shoulder_stress = min(1.0, (exercise_data['pushups'] * 0.01)) # Default minor stress

    muscle_values = {
        'quads': quads,
        'glutes': glutes,
        'chest': chest,
        'triceps': triceps,
        'calves': calves,
        'core': core,
        'knee_stress': knee_stress,
        'back_stress': back_stress,
        'shoulder_stress': shoulder_stress
    }

    # 3. Three.js HTML/JS Integration
    three_js_code = f"""
    <div id="three-container" style="width: 100%; height: 500px; background: radial-gradient(circle, #1a1a2e 0%, #16213e 100%); border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); overflow: hidden; position: relative;">
        <div id="controls" style="position: absolute; top: 10px; left: 10px; z-index: 100; color: white; font-family: sans-serif; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 8px; font-size: 12px;">
            <div style="font-weight: bold; margin-bottom: 5px;">View Mode:</div>
            <button id="btn-target" onclick="setView('target')" style="background: #4ecca3; border: none; padding: 5px 10px; border-radius: 4px; color: white; cursor: pointer; margin-right: 5px;">🔥 Target</button>
            <button id="btn-stress" onclick="setView('stress')" style="background: rgba(255,255,255,0.1); border: none; padding: 5px 10px; border-radius: 4px; color: white; cursor: pointer;">⚠️ Stress</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const muscleData = {json.dumps(muscle_values)};
        let currentMode = 'target';
        
        const container = document.getElementById('three-container');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 500, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(container.clientWidth, 500);
        container.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
        directionalLight.position.set(2, 5, 5);
        scene.add(directionalLight);
        
        const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
        backLight.position.set(-2, -2, -5);
        scene.add(backLight);

        // Group for rotation
        const bodyGroup = new THREE.Group();
        scene.add(bodyGroup);

        // Materials setup
        const materials = {{
            base: new THREE.MeshPhongMaterial({{ color: 0x777777, transparent: true, opacity: 0.3, shininess: 30 }}),
            head: new THREE.MeshPhongMaterial({{ color: 0x777777, shininess: 50 }}),
            quads: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            glutes: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            chest: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            triceps: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            calves: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            core: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            knees: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            back: new THREE.MeshPhongMaterial({{ color: 0x777777 }}),
            shoulders: new THREE.MeshPhongMaterial({{ color: 0x777777 }})
        }};

        function getColor(intensity, isStress) {{
            // Use HSL for smooth transitions
            const hue = isStress ? 0 : 150; // Red for stress, Green-ish for target
            const sat = 70 + (intensity * 30);
            const lgt = 40 + (intensity * 20);
            return new THREE.Color(`hsl(${{hue}}, ${{sat}}%, ${{lgt}}%)`);
        }}

        function updateMaterials() {{
            const isS = currentMode === 'stress';
            const neutral = new THREE.Color(0x777777);
            
            // Highlight buttons
            document.getElementById('btn-target').style.background = isS ? 'rgba(255,255,255,0.1)' : '#4ecca3';
            document.getElementById('btn-stress').style.background = isS ? '#e94560' : 'rgba(255,255,255,0.1)';

            if (!isS) {{
                materials.quads.color = getColor(muscleData.quads, false);
                materials.glutes.color = getColor(muscleData.glutes, false);
                materials.chest.color = getColor(muscleData.chest, false);
                materials.triceps.color = getColor(muscleData.triceps, false);
                materials.calves.color = getColor(muscleData.calves, false);
                materials.core.color = getColor(muscleData.core, false);
                materials.back.color = neutral;
                materials.knees.color = neutral;
                materials.shoulders.color = neutral;
            }} else {{
                materials.quads.color = neutral;
                materials.glutes.color = neutral;
                materials.chest.color = neutral;
                materials.triceps.color = neutral;
                materials.calves.color = neutral;
                materials.core.color = neutral;
                materials.back.color = getColor(muscleData.back_stress, true);
                materials.knees.color = getColor(muscleData.knee_stress, true);
                materials.shoulders.color = getColor(muscleData.shoulder_stress, true);
            }}
        }}

        // Body Construction (Minimalist Stylized Human)
        // Torso
        const torsoGeom = new THREE.BoxGeometry(0.6, 1, 0.3);
        const torso = new THREE.Mesh(torsoGeom, materials.base);
        bodyGroup.add(torso);

        // Chest Plate
        const chestGeom = new THREE.BoxGeometry(0.5, 0.4, 0.1);
        const chest = new THREE.Mesh(chestGeom, materials.chest);
        chest.position.set(0, 0.25, 0.15);
        bodyGroup.add(chest);

        // Core
        const coreGeom = new THREE.BoxGeometry(0.4, 0.3, 0.05);
        const core = new THREE.Mesh(coreGeom, materials.core);
        core.position.set(0, -0.2, 0.15);
        bodyGroup.add(core);

        // Head
        const headGeom = new THREE.BoxGeometry(0.3, 0.35, 0.3);
        const head = new THREE.Mesh(headGeom, materials.head);
        head.position.y = 0.75;
        bodyGroup.add(head);

        // Arms
        const armGeom = new THREE.BoxGeometry(0.15, 0.8, 0.15);
        const armL = new THREE.Mesh(armGeom, materials.triceps);
        armL.position.set(-0.45, 0.1, 0);
        bodyGroup.add(armL);
        const armR = new THREE.Mesh(armGeom, materials.triceps);
        armR.position.set(0.45, 0.1, 0);
        bodyGroup.add(armR);

        // Shoulders
        const shoulderGeom = new THREE.SphereGeometry(0.12, 12, 12);
        const shoulderL = new THREE.Mesh(shoulderGeom, materials.shoulders);
        shoulderL.position.set(-0.45, 0.45, 0);
        bodyGroup.add(shoulderL);
        const shoulderR = new THREE.Mesh(shoulderGeom, materials.shoulders);
        shoulderR.position.set(0.45, 0.45, 0);
        bodyGroup.add(shoulderR);

        // Legs
        const upperLegGeom = new THREE.BoxGeometry(0.22, 0.7, 0.22);
        const legUL = new THREE.Mesh(upperLegGeom, materials.quads);
        legUL.position.set(-0.2, -0.8, 0);
        bodyGroup.add(legUL);
        const legUR = new THREE.Mesh(upperLegGeom, materials.quads);
        legUR.position.set(0.2, -0.8, 0);
        bodyGroup.add(legUR);

        // Glutes
        const gluteGeom = new THREE.BoxGeometry(0.55, 0.35, 0.15);
        const glutes = new THREE.Mesh(gluteGeom, materials.glutes);
        glutes.position.set(0, -0.5, -0.15);
        bodyGroup.add(glutes);

        // Knees
        const kneeGeom = new THREE.SphereGeometry(0.1, 8, 8);
        const kneeL = new THREE.Mesh(kneeGeom, materials.knees);
        kneeL.position.set(-0.2, -1.15, 0.1);
        bodyGroup.add(kneeL);
        const kneeR = new THREE.Mesh(kneeGeom, materials.knees);
        kneeR.position.set(0.2, -1.15, 0.1);
        bodyGroup.add(kneeR);

        // Lower Legs
        const lowerLegGeom = new THREE.BoxGeometry(0.18, 0.7, 0.18);
        const calfL = new THREE.Mesh(lowerLegGeom, materials.calves);
        calfL.position.set(-0.2, -1.5, 0);
        bodyGroup.add(calfL);
        const calfR = new THREE.Mesh(lowerLegGeom, materials.calves);
        calfR.position.set(0.2, -1.5, 0);
        bodyGroup.add(calfR);

        // Back
        const backGeom = new THREE.BoxGeometry(0.45, 0.7, 0.05);
        const back = new THREE.Mesh(backGeom, materials.back);
        back.position.set(0, 0.1, -0.16);
        bodyGroup.add(back);

        camera.position.z = 4.5;
        camera.position.y = -0.5;

        // Interaction Logic
        let isDragging = false;
        let previousMouseX = 0;
        let rotationVelocity = 0.01; // Current rotation speed

        container.addEventListener('mousedown', (e) => {{
            isDragging = true;
            previousMouseX = e.clientX;
        }});

        window.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        window.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                const deltaX = e.clientX - previousMouseX;
                bodyGroup.rotation.y += deltaX * 0.01;
                previousMouseX = e.clientX;
                rotationVelocity = 0; // Pause auto-rotation on interaction
            }}
        }});

        // Touch support
        container.addEventListener('touchstart', (e) => {{
            isDragging = true;
            previousMouseX = e.touches[0].clientX;
        }}, {{ passive: true }});

        window.addEventListener('touchend', () => {{
            isDragging = false;
        }});

        window.addEventListener('touchmove', (e) => {{
            if (isDragging) {{
                const deltaX = e.touches[0].clientX - previousMouseX;
                bodyGroup.rotation.y += deltaX * 0.01;
                previousMouseX = e.touches[0].clientX;
                rotationVelocity = 0;
            }}
        }}, {{ passive: true }});

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            if (!isDragging) {{
                bodyGroup.rotation.y += rotationVelocity;
                // Slowly resume auto-rotation if it was stopped
                if (rotationVelocity < 0.005) rotationVelocity += 0.0001;
            }}
            renderer.render(scene, camera);
        }}

        window.setView = function(mode) {{
            currentMode = mode;
            updateMaterials();
        }};

        updateMaterials();
        animate();

        // Handle Resizing
        window.addEventListener('resize', () => {{
            const newWidth = container.clientWidth;
            renderer.setSize(newWidth, 500);
            camera.aspect = newWidth / 500;
            camera.updateProjectionMatrix();
        }});
    </script>
    """
    
    components.html(three_js_code, height=520)

def heatmap_page_v2():
    """Enhanced Heatmap Page with 3D Component"""
    st.title("🦾 Muscle Engagement & Stress")
    st.markdown("---")
    
    if 'user_id' not in st.session_state:
        st.warning("Please log in to see your personalized muscle map.")
        return

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Interactive 3D Avatar")
        render_3d_heatmap(st.session_state.user_id)
        st.info("💡 **Drag to rotate** the model. Toggle modes in the top corner to see stress vs engagement.")
        
    with col2:
        st.subheader("Performance Insights")
        
        db = Database()
        user_stats = db.get_user_stats(st.session_state.user_id)
        
        if user_stats:
            j = user_stats.get('total_jumps', 0) or 0
            s = user_stats.get('total_squats', 0) or 0
            p = user_stats.get('total_pushups', 0) or 0
            bad = user_stats.get('total_bad_moves', 0) or 0
            
            st.write("**Top Engagement Zones**")
            # Dynamic progress bars
            total = max(1, s + j + p)
            lower_body_pct = (s + j) / total
            upper_body_pct = p / total
            
            st.write(f"🦵 Lower Body ({lower_body_pct:.0%})")
            st.progress(min(1.0, (s + j) / 500))
            
            st.write(f"💪 Upper Body ({upper_body_pct:.0%})")
            st.progress(min(1.0, p / 200))
            
            st.markdown("---")
            st.write("**⚠️ Joint Stress Level**")
            if bad > 0:
                stress_pct = min(1.0, bad / 50)
                st.write(f"Stress Intensity: {stress_pct:.0%}")
                st.progress(stress_pct)
                st.warning("Recommendation: Focus on landing softly and keeping knees aligned.")
            else:
                st.success("Perfect alignment detected. Joint stress is minimal.")
        else:
            st.info("No data recorded yet. Start a session to see insights!")

