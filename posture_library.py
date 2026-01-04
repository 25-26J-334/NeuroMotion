"""
Posture Library and Learning System for AI Athlete Trainer
Provides posture examples, tips, and learning modules for better form
"""
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class PostureLibrary:
    """Manages posture examples and learning content"""
    
    def __init__(self):
        self.postures = self._load_postures()
        self.learning_modules = self._load_learning_modules()
    
    def _load_postures(self) -> Dict[str, List[Dict]]:
        """Load posture examples from data"""
        return {
            'jump': [
                {
                    'name': 'Basic Jump',
                    'difficulty': 'Beginner',
                    'description': 'Standard vertical jump with proper arm swing',
                    'key_points': [
                        'Start with feet shoulder-width apart',
                        'Bend knees to 45-degree angle',
                        'Swing arms upward explosively',
                        'Land softly with bent knees'
                    ],
                    'common_mistakes': [
                        'Not bending knees enough',
                        'Landing with straight legs',
                        'Not using arm swing'
                    ],
                    'tips': [
                        'Focus on explosive hip extension',
                        'Practice landing mechanics first',
                        'Use visualization techniques'
                    ]
                },
                {
                    'name': 'Box Jump',
                    'difficulty': 'Intermediate',
                    'description': 'Jump onto an elevated surface safely',
                    'key_points': [
                        'Approach box with controlled speed',
                        'Explosive jump from balls of feet',
                        'Land softly in center of box',
                        'Step down, don\'t jump down'
                    ],
                    'common_mistakes': [
                        'Jumping too high for current ability',
                        'Landing too close to edge',
                        'Jumping down from box'
                    ],
                    'tips': [
                        'Start with low box height',
                        'Focus on landing technique',
                        'Progress gradually'
                    ]
                },
                {
                    'name': 'Depth Jump',
                    'difficulty': 'Advanced',
                    'description': 'Jump down from height and immediately jump upward',
                    'key_points': [
                        'Step off box (don\'t jump)',
                        'Land on balls of feet',
                        'Minimize ground contact time',
                        'Explode upward immediately'
                    ],
                    'common_mistakes': [
                        'Too much ground contact time',
                        'Landing flat-footed',
                        'Not ready for impact'
                    ],
                    'tips': [
                        'Master box jumps first',
                        'Start with low height (12-18 inches)',
                        'Focus on reactive strength'
                    ]
                }
            ],
            'squat': [
                {
                    'name': 'Bodyweight Squat',
                    'difficulty': 'Beginner',
                    'description': 'Fundamental squat movement without weights',
                    'key_points': [
                        'Feet shoulder-width apart',
                        'Chest up and back straight',
                        'Sit back as if sitting in chair',
                        'Thighs parallel to ground or lower'
                    ],
                    'common_mistakes': [
                        'Knees extending past toes',
                        'Rounding lower back',
                        'Not going low enough'
                    ],
                    'tips': [
                        'Practice with chair behind you',
                        'Keep weight on heels',
                        'Drive up through heels'
                    ]
                },
                {
                    'name': 'Jump Squat',
                    'difficulty': 'Intermediate',
                    'description': 'Explosive squat with jump at top',
                    'key_points': [
                        'Lower into squat position',
                        'Explode upward through heels',
                        'Tuck knees to chest in air',
                        'Land softly and repeat'
                    ],
                    'common_mistakes': [
                        'Not using full range of motion',
                        'Landing stiffly',
                        'Not exploding upward'
                    ],
                    'tips': [
                        'Start with bodyweight only',
                        'Focus on landing mechanics',
                        'Use arm swing for momentum'
                    ]
                },
                {
                    'name': 'Pistol Squat',
                    'difficulty': 'Advanced',
                    'description': 'Single-leg squat requiring balance and strength',
                    'key_points': [
                        'Stand on one leg',
                        'Extend other leg forward',
                        'Lower slowly with control',
                        'Keep chest up throughout'
                    ],
                    'common_mistakes': [
                        'Losing balance',
                        'Not going low enough',
                        'Rounding back'
                    ],
                    'tips': [
                        'Use support for balance initially',
                        'Practice assisted pistol squats',
                        'Build flexibility first'
                    ]
                }
            ],
            'pushup': [
                {
                    'name': 'Standard Push-up',
                    'difficulty': 'Beginner',
                    'description': 'Classic upper body exercise',
                    'key_points': [
                        'Hands slightly wider than shoulders',
                        'Body in straight line from head to heels',
                        'Lower chest to floor',
                        'Push back up to starting position'
                    ],
                    'common_mistakes': [
                        'Sagging hips',
                        'Not going low enough',
                        'Flaring elbows too wide'
                    ],
                    'tips': [
                        'Keep core engaged',
                        'Control the movement',
                        'Breathe out on push up'
                    ]
                },
                {
                    'name': 'Diamond Push-up',
                    'difficulty': 'Intermediate',
                    'description': 'Close-grip push-up targeting triceps',
                    'key_points': [
                        'Place hands close together forming diamond',
                        'Index fingers and thumbs touching',
                        'Keep elbows close to body',
                        'Lower chest to hands'
                    ],
                    'common_mistakes': [
                        'Hands too far apart',
                        'Elbows flaring out',
                        'Not full range of motion'
                    ],
                    'tips': [
                        'Build up to it gradually',
                        'Focus on triceps engagement',
                        'Maintain proper form'
                    ]
                },
                {
                    'name': 'Clapping Push-up',
                    'difficulty': 'Advanced',
                    'description': 'Explosive push-up with hand clap',
                    'key_points': [
                        'Perform standard push-up',
                        'Explode upward forcefully',
                        'Clap hands in air',
                        'Land with soft elbows'
                    ],
                    'common_mistakes': [
                        'Not enough explosive power',
                        'Landing with locked elbows',
                        'Losing body tension'
                    ],
                    'tips': [
                        'Master regular push-ups first',
                        'Practice on elevated surface',
                        'Focus on power generation'
                    ]
                }
            ]
        }
    
    def _load_learning_modules(self) -> List[Dict]:
        """Load learning modules for posture improvement"""
        return [
            {
                'id': 'posture_fundamentals',
                'title': 'Posture Fundamentals',
                'description': 'Learn the basics of proper posture for all exercises',
                'difficulty': 'Beginner',
                'duration_minutes': 15,
                'exercises': ['jump', 'squat', 'pushup'],
                'content': [
                    {
                        'type': 'text',
                        'title': 'Understanding Proper Posture',
                        'content': 'Proper posture is the foundation of effective exercise performance and injury prevention.'
                    },
                    {
                        'type': 'checklist',
                        'title': 'Universal Posture Principles',
                        'items': [
                            'Maintain neutral spine position',
                            'Keep shoulders back and down',
                            'Engage core muscles',
                            'Breathe properly throughout movement',
                            'Move through full range of motion'
                        ]
                    },
                    {
                        'type': 'practice',
                        'title': 'Practice Exercise',
                        'content': 'Stand against wall to check alignment: heels, glutes, shoulders, and head should touch the wall.'
                    }
                ]
            },
            {
                'id': 'balance_and_stability',
                'title': 'Balance and Stability',
                'description': 'Improve balance and stability for better exercise form',
                'difficulty': 'Intermediate',
                'duration_minutes': 20,
                'exercises': ['jump', 'squat'],
                'content': [
                    {
                        'type': 'text',
                        'title': 'Why Balance Matters',
                        'content': 'Good balance allows for better force transfer and reduces injury risk.'
                    },
                    {
                        'type': 'drills',
                        'title': 'Balance Drills',
                        'drills': [
                            'Single leg stance: 30 seconds each leg',
                            'Tightrope walk: heel-to-toe walking',
                            'Balance board exercises',
                            'Yoga tree pose variations'
                        ]
                    }
                ]
            },
            {
                'id': 'explosive_power',
                'title': 'Explosive Power Development',
                'description': 'Learn techniques for explosive movements',
                'difficulty': 'Advanced',
                'duration_minutes': 25,
                'exercises': ['jump', 'squat', 'pushup'],
                'content': [
                    {
                        'type': 'text',
                        'title': 'Power vs Strength',
                        'content': 'Power is strength applied quickly. Essential for athletic performance.'
                    },
                    {
                        'type': 'techniques',
                        'title': 'Power Generation Techniques',
                        'techniques': [
                            'Plyometric progressions',
                            'Olympic lift variations',
                            'Medicine ball throws',
                            'Resistance band explosions'
                        ]
                    }
                ]
            }
        ]
    
    def get_postures_by_exercise(self, exercise_type: str) -> List[Dict]:
        """Get posture examples for specific exercise"""
        return self.postures.get(exercise_type, [])
    
    def get_all_postures(self) -> Dict[str, List[Dict]]:
        """Get all posture examples"""
        return self.postures
    
    def get_learning_modules(self, difficulty: str = None, exercise: str = None) -> List[Dict]:
        """Get learning modules with optional filtering"""
        modules = self.learning_modules
        
        if difficulty:
            modules = [m for m in modules if m['difficulty'] == difficulty]
        
        if exercise:
            modules = [m for m in modules if exercise in m['exercises']]
        
        return modules
    
    def get_module_by_id(self, module_id: str) -> Dict:
        """Get specific learning module by ID"""
        for module in self.learning_modules:
            if module['id'] == module_id:
                return module
        return {}


def posture_library_page():
    """Display posture library page"""
    st.title("🧘‍♂️ Posture Library")
    st.markdown("Master proper form and technique with our comprehensive posture guides")
    
    # Initialize posture library
    if 'posture_library' not in st.session_state:
        st.session_state.posture_library = PostureLibrary()
    
    library = st.session_state.posture_library
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Posture Guide", "🎓 Learning Modules", "📊 Progress Tracker", "🎯 Practice Mode"])
    
    with tab1:
        st.markdown("### Exercise Posture Guides")
        
        # Exercise type selector
        exercise_type = st.selectbox(
            "Select Exercise Type:",
            ["all", "jump", "squat", "pushup"],
            format_func=lambda x: {"all": "All Exercises", "jump": "🏃 Jumps", "squat": "🦵 Squats", "pushup": "💪 Push-ups"}[x]
        )
        
        if exercise_type == "all":
            # Show all exercises
            for ex_type in ["jump", "squat", "pushup"]:
                st.markdown(f"#### {'🏃 Jumps' if ex_type == 'jump' else '🦵 Squats' if ex_type == 'squat' else '💪 Push-ups'}")
                postures = library.get_postures_by_exercise(ex_type)
                
                for posture in postures:
                    with st.expander(f"{posture['name']} ({posture['difficulty']})"):
                        st.markdown(f"**Description:** {posture['description']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Key Points:**")
                            for point in posture['key_points']:
                                st.markdown(f"• {point}")
                        
                        with col2:
                            st.markdown("**Common Mistakes:**")
                            for mistake in posture['common_mistakes']:
                                st.markdown(f"• {mistake}")
                        
                        st.markdown("**Tips:**")
                        for tip in posture['tips']:
                            st.markdown(f"💡 {tip}")
        else:
            # Show specific exercise
            postures = library.get_postures_by_exercise(exercise_type)
            
            if postures:
                for posture in postures:
                    with st.expander(f"{posture['name']} ({posture['difficulty']})"):
                        st.markdown(f"**Description:** {posture['description']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Key Points:**")
                            for point in posture['key_points']:
                                st.markdown(f"• {point}")
                        
                        with col2:
                            st.markdown("**Common Mistakes:**")
                            for mistake in posture['common_mistakes']:
                                st.markdown(f"• {mistake}")
                        
                        st.markdown("**Tips:**")
                        for tip in posture['tips']:
                            st.markdown(f"💡 {tip}")
            else:
                st.info("No postures found for this exercise type.")
    
    with tab2:
        st.markdown("### 🎓 Learning Modules")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            difficulty_filter = st.selectbox(
                "Filter by Difficulty:",
                ["all", "Beginner", "Intermediate", "Advanced"]
            )
        
        with col2:
            exercise_filter = st.selectbox(
                "Filter by Exercise:",
                ["all", "jump", "squat", "pushup"],
                format_func=lambda x: {"all": "All", "jump": "Jumps", "squat": "Squats", "pushup": "Push-ups"}[x]
            )
        
        # Get filtered modules
        modules = library.get_learning_modules(
            difficulty=difficulty_filter if difficulty_filter != "all" else None,
            exercise=exercise_filter if exercise_filter != "all" else None
        )
        
        if modules:
            for module in modules:
                with st.expander(f"{module['title']} ({module['difficulty']}) - {module['duration_minutes']} min"):
                    st.markdown(f"**Description:** {module['description']}")
                    st.markdown(f"**Exercises:** {', '.join(module['exercises'].title() for ex in module['exercises'])}")
                    
                    if st.button(f"Start Module: {module['title']}", key=f"start_{module['id']}"):
                        st.session_state.current_module = module['id']
                        st.rerun()
        else:
            st.info("No learning modules found with selected filters.")
    
    with tab3:
        st.markdown("### 📊 Posture Progress Tracker")
        
        # Placeholder for progress tracking
        st.info("Progress tracking feature coming soon! This will show your posture improvement over time.")
        
        # Mock progress data for demonstration
        progress_data = {
            'Date': pd.date_range(end=datetime.now(), periods=10, freq='D'),
            'Posture Score': [65, 68, 72, 70, 75, 78, 82, 80, 85, 88],
            'Exercise': ['Jump', 'Squat', 'Push-up', 'Jump', 'Squat', 'Push-up', 'Jump', 'Squat', 'Push-up', 'Jump']
        }
        
        df = pd.DataFrame(progress_data)
        
        fig = px.line(df, x='Date', y='Posture Score', color='Exercise', 
                     title='Posture Quality Score Over Time')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### 🎯 Practice Mode")
        
        # Exercise selection for practice
        practice_exercise = st.selectbox(
            "Select Exercise to Practice:",
            ["jump", "squat", "pushup"],
            format_func=lambda x: {"jump": "🏃 Jump", "squat": "🦵 Squat", "pushup": "💪 Push-up"}[x]
        )
        
        # Get postures for selected exercise
        postures = library.get_postures_by_exercise(practice_exercise)
        
        if postures:
            selected_posture = st.selectbox(
                "Select Posture Variation:",
                options=range(len(postures)),
                format_func=lambda x: f"{postures[x]['name']} ({postures[x]['difficulty']})"
            )
            
            posture = postures[selected_posture]
            
            st.markdown(f"#### {posture['name']} Practice")
            st.markdown(f"**Difficulty:** {posture['difficulty']}")
            st.markdown(f"**Description:** {posture['description']}")
            
            # Practice checklist
            st.markdown("**Practice Checklist:**")
            checked_items = []
            for i, point in enumerate(posture['key_points']):
                if st.checkbox(point, key=f"practice_{i}"):
                    checked_items.append(point)
            
            # Progress indicator
            progress = len(checked_items) / len(posture['key_points']) * 100
            st.progress(progress / 100)
            st.markdown(f"**Progress:** {len(checked_items)}/{len(posture['key_points'])} completed")
            
            if progress == 100:
                st.success("🎉 Excellent! You've mastered all key points for this posture!")
                if st.button("Mark as Completed"):
                    # Save completion to session state
                    if 'completed_postures' not in st.session_state:
                        st.session_state.completed_postures = []
                    
                    completion = {
                        'posture': posture['name'],
                        'exercise': practice_exercise,
                        'completed_at': datetime.now()
                    }
                    st.session_state.completed_postures.append(completion)
                    st.success("Posture marked as completed!")
        else:
            st.info("No postures available for this exercise.")


def show_posture_tips_during_training(exercise_type: str):
    """Show posture tips during training sessions"""
    if 'posture_library' not in st.session_state:
        st.session_state.posture_library = PostureLibrary()
    
    library = st.session_state.posture_library
    postures = library.get_postures_by_exercise(exercise_type)
    
    if postures:
        # Show beginner posture tips
        beginner_posture = next((p for p in postures if p['difficulty'] == 'Beginner'), postures[0])
        
        st.markdown("### 🧘‍♂️ Quick Posture Tips")
        st.markdown(f"**{beginner_posture['name']} Form Reminders:**")
        
        # Show top 3 key points
        for point in beginner_posture['key_points'][:3]:
            st.markdown(f"• {point}")
        
        st.markdown("---")


def add_posture_achievements():
    """Add posture-related achievements to the system"""
    achievements = [
        {
            'id': 'posture_beginner',
            'name': 'Posture Novice',
            'description': 'Complete your first posture learning module',
            'icon': '🧘‍♂️',
            'requirement': 'Complete 1 learning module'
        },
        {
            'id': 'posture_intermediate',
            'name': 'Form Master',
            'description': 'Complete 5 posture learning modules',
            'icon': '🏆',
            'requirement': 'Complete 5 learning modules'
        },
        {
            'id': 'posture_expert',
            'name': 'Posture Guru',
            'description': 'Complete all posture learning modules',
            'icon': '👑',
            'requirement': 'Complete all learning modules'
        },
        {
            'id': 'perfect_form',
            'name': 'Perfect Form',
            'description': 'Achieve 95%+ posture score in 10 sessions',
            'icon': '⭐',
            'requirement': 'Maintain excellent form'
        }
    ]
    
    return achievements


if __name__ == "__main__":
    # Test the posture library
    library = PostureLibrary()
    print("Posture Library initialized successfully")
    print(f"Loaded {len(library.get_all_postures())} exercise categories")
    print(f"Loaded {len(library.get_learning_modules())} learning modules")
