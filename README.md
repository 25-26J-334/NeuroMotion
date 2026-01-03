# Athlete Performance and Training AI-Based System

- **Project ID:** 25-26J-334  
- **Team:** Manulakshan_IT22283962 | Mathumitha_IT21379338 | Sylvester_IT22311368 | Jude Jawakker_IT22330864
- **Git repository:** https://github.com/25-26J-334/NeuroMotion.git
- **Course:** IT4010 – Research Project (2025 July)  
- **Specialization:** Information Technology (IT)  
- **Research Group:** Software Systems & Technologies (SST)  
- **Institution:** Sri Lanka Institute of Information Technology (SLIIT)

---

## 1. Overview

The **Athlete Performance and Training AI-Based System** is a video-driven, AI-powered platform designed to monitor, analyze, and enhance athlete performance without relying on intrusive wearable devices. The system uses **computer vision**, **machine learning**, and **intelligent training recommendations** to deliver real-time, sport-specific insights to athletes, coaches, and sports institutions.

### 1.1 Motivation

Traditional athlete monitoring approaches have several limitations:

- Manual observation by coaches is **subjective** and **inconsistent**.
- Wearable sensors can be **intrusive**, **uncomfortable**, and **expensive**.
- Existing AI tools often lack **sport-specific context** and **real-time, actionable insights**.
- There is limited use of **predictive analytics** and **adaptive training** in many training environments.

This project aims to address these gaps by creating a **wearable-free, video-based AI system** that can:

- Analyze form and technique in real time.
- Predict performance trends and injury risks.
- Recommend adaptive, personalized training plans.
- Serve as a foundational framework for sports analytics research in Sri Lanka.

---

## 2. Problem Statement

Current athlete performance monitoring solutions suffer from one or more of the following issues:

1. **Subjectivity and inconsistency** in coach-driven assessments.
2. **High dependency on wearables and sensors**, which can be costly and impractical in many training environments.
3. **Lack of sport-specific AI models**, resulting in generic or non-actionable insights.
4. **Limited predictive capability**, focusing mostly on descriptive statistics rather than proactive injury prevention or performance optimization.
5. **Fragmented systems**, where data acquisition, analysis, and visualization are not integrated into a cohesive workflow.

### Research Gap

There is a need for an **integrated, sport-specific, video-driven AI system** that:

- Uses **computer vision** for real-time pose and technique analysis.
- Uses **machine learning** to forecast performance and identify injury risks.
- Provides **adaptive, data-driven training recommendations**.
- Integrates all components into a **single, coherent platform** accessible via a modern web interface.

---

## 3. Project Objectives

### 3.1 Main Objective

To **design and develop an AI-powered system** that enhances athlete performance by collecting, analyzing, and interpreting multimodal training data (primarily video), enabling:

- Predictive insights  
- Injury prevention  
- Technique correction  
- Personalized training recommendations  

### 3.2 Sub Objectives

1. **Data Pipeline & Integration System**  
   - Design and implement a robust data acquisition and preprocessing pipeline for sports video and related data.

2. **Computer Vision for Form & Technique Analysis**  
   - Implement pose estimation and biomechanical analysis for real-time detection of technique errors.

3. **AI Models for Performance Prediction**  
   - Develop machine learning models to predict athlete performance trends and injury risk.

4. **Personalized Training & Visualization System**  
   - Build a user-friendly dashboard and intelligent recommender that delivers adaptive training plans and feedback.

---

## 4. System Architecture

### 4.1 High-Level Architecture Diagram

```text
                         ┌────────────────────────────────────┐
                         │        DATA SOURCES                 │
                         │-------------------------------------│
                         │ -  Live training camera feeds        │
                         │ -  Uploaded training videos          │
                         │ -  Public sports datasets            │
                         │   (SportsPose, AthletePose3D, etc.)│
                         └───────────────┬─────────────────────┘
                                         │
                                         ▼
                 ┌─────────────────────────────────────────────┐
                 │   COMPONENT 1: DATA PIPELINE & INTEGRATION  │
                 │   (Preprocessing, normalization, metadata)  │
                 └───────────────┬─────────────────────────────┘
                                 │
                                 ▼
                ┌──────────────────────────────────────────────┐
                │ COMPONENT 2: COMPUTER VISION & POSE ANALYSIS │
                │ (Pose estimation, joint angles, form errors) │
                └────────────────┬─────────────────────────────┘
                                 │
                                 ▼
          ┌─────────────────────────────────────────────────────────┐
          │   COMPONENT 3: PERFORMANCE PREDICTION MODELS           │
          │ (Trend forecasting, injury risk, anomaly detection)    │
          └─────────────────────┬──────────────────────────────────┘
                                │
                                ▼
          ┌─────────────────────────────────────────────────────────┐
          │ COMPONENT 4: DASHBOARD & TRAINING RECOMMENDER          │
          │ (Visualization, RL-based adaptive plans, chatbot, etc.)│
          └─────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────────────┐
                    │        END USERS                │
                    │---------------------------------│
                    │ -  Athletes                      │
                    │ -  Coaches                       │
                    │ -  Sports institutions           │
                    └────────────────────────────────┘
```

---

### 4.2 Data Flow

1. **Raw video data is ingested from cameras, uploaded files, or public datasets.**
   
2. **The Data Pipeline component preprocesses videos:**
   - Standardizes formats & resolutions
   - Extracts frames
   - Aligns multi-camera angles
   - Annotates with metadata (player, context, session info)
     
3. **The Computer Vision component:**
   - Runs pose estimation (MediaPipe/OpenPose, etc.)
   - Extracts skeletal keypoints and calculates joint angles
   - Identifies deviations from optimal technique
     
4. **ML models:**
   - Use historical and current features to predict performance, fatigue, injury risk, and trends.

5. **The Dashboard & Recommender:**
   - Visualizes metrics
   - Shows real-time corrective feedback
   - Suggests personalized training plans (e.g., using RL)
   - Logs and tracks progress over time

---

## 5. Modules and Responsibilities

### 5.1 Component 1 – Data Pipeline & Integration System

**Member: Y. Manulakshan (IT22283962)**
   - Multi-source video acquisition (live feeds, uploads, datasets)
   - Video preprocessing and normalization (resolution, frame rate, noise removal)
   - Frame extraction and multi-view synchronization
   - Metadata annotation (athlete, session, context)
   - Data storage and API integration for downstream modules

### 5.2 Component 2 – Computer Vision for Form & Technique Analysis

**Member: G. Mathumitha (IT21379338)**
   - Pose estimation using MediaPipe / OpenPose
   - Keypoint extraction and joint angle computation
   - Technique error detection (e.g., incorrect posture, misaligned joints)
   - Real-time feedback generation (e.g., “Increase knee drive”, “Correct hip alignment”)
   - Integration of visual overlays and metrics for the dashboard

### 5.3 Component 3 – AI Models for Performance Prediction

**Member: L. M. Sylvester (IT22311368)**
   - Feature engineering from pose data and training logs
   - Regression models for performance forecasting
   - Classification models for injury/fatigue risk
   - Anomaly detection for unusual patterns
   - Model evaluation, tuning, and performance reporting

### 5.4 Component 4 – Personalized Training & Visualization System

**Member: G. Jude Jawakker (IT22330864)**
   - Web-based dashboard for performance visualization
   - Real-time feedback display and alerting
   - Adaptive training recommender (e.g., using Reinforcement Learning or decision trees)
   - Progress tracking and historical analytics
   - Chatbot integration for question–answer style interactions
