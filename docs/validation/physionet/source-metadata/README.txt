Title:
Neurophysiological Dataset of Stress Resilience During Human-Computer Interaction

Description:
This dataset provides multimodal neurophysiological and physiological recordings collected to investigate stress resilience during a computer-based task. The dataset includes electroencephalography (EEG), functional near-infrared spectroscopy (fNIRS), electrodermal activity (EDA), blood volume pulse (BVP), inter-beat intervals (IBI), heart rate (HR), accelerometer (ACC) data, and eye-tracking measurements.

During the experiment, participants performed tasks using the Multi-Attribute Task Battery-II (MATB-II), a validated human performance and cognitive workload assessment tool.

Study Protocol:
Participants completed the following six sequential conditions (total ~31 minutes):

Resting Baseline (1 min)

Working Baseline (6 min) – RESMAN task only

Stress 1 (6 min) – RESMAN + COMMS tasks

Recovery 1 (6 min) – RESMAN only

Stress 2 (6 min) – RESMAN + COMMS

Recovery 2 (6 min) – RESMAN only


This dataset includes event markers synchronized across all modalities to track task condition transitions. Additionally, subjective resilience was assessed using the 10-item Connor-Davidson Resilience Scale (CD-RISC), and demographic variables such as age, gender, and ethnic background were recorded.

Folder Structure:
/StressResilience_Dataset/
│
├── demographicCDrisk.csv             # Demographics + CD-RISC resilience scores
├── EEG_32_Channel_mapping.xyz        # 3D EEG electrode coordinates (10-20 system)
├── fNIRS_frontal.xyz                 # 3D coordinates for fNIRS optodes (frontal region)
│
├── MATB-II/                          # Task performance data (fuel levels)
│   ├── p01resman.csv
│   ├── ...
│
├── PPG/                              # Empatica E4 physiological recordings
│   ├── p01/
│   │   ├── ACC.csv                   # 3-axis accelerometer (X, Y, Z)
│   │   ├── BVP.csv                   # Blood volume pulse (PPG signal)
│   │   ├── EDA.csv                   # Electrodermal activity
│   │   ├── HR.csv                    # Heart rate (BPM)
│   │   ├── IBI.csv                   # Inter-beat intervals (s)
│   │   ├── TEMP.csv                  # Skin temperature (°C)
│   │   ├── tags.csv                  # Event marker (Working Baseline start)
│   │   └── info.txt                  # Session metadata (Unix start time, device info)
│   ├── ...
│
├── EEGfNIRSeye_p1-p15.zip            # EEG, fNIRS, eye tracking data for p01–p15
├── EEGfNIRSeye_p16-p25.zip           # EEG, fNIRS, eye tracking data for p16–p25
├── EEGfNIRSeye_p26-p37.zip           # EEG, fNIRS, eye tracking data for p26–p37
│
└── README.txt                        # Dataset overview and usage instructions (this file)

Data Access & Usage Notes:

Each participant’s data is organized by subject ID (e.g., p01, p02, ...).

EEG, fNIRS, and eye-tracking data are stored in .csv format within the zipped folders and contain 74 rows of synchronized recordings per sample.

Empatica E4 data (PPG) is stored in separate participant folders under /PPG/.

Task performance is logged in the /MATB-II/ folder.

Use the provided .xyz files for sensor localization and topographical analysis.

Note: Event markers are provided every 6 minutes to align the recordings with the six task conditions. Some participants may have additional/missing markers due to recording anomalies, which are documented in the notes.

Sampling Rates:

EEG/fNIRS/Eye tracking (p01–p24): 250 Hz

Eye tracking only (p25–p37): 50 Hz (separately recorded using Tobii Glasses)

Applications:


The dataset can be used for neuroergonomics research, machine learning applications in stress resilience modeling, and human factors studies. Researchers can leverage this dataset to analyze neural and physiological responses under stress, develop predictive models, and evaluate adaptive training interventions.

Limitations:

Eye-tracking desynchronization: For p25–p37, eye data is asynchronous with EEG/fNIRS.

No starter code provided: Preprocessing or analysis scripts are not included but can be requested from the authors.

Sample size: The dataset includes 35 participants, ideal for exploratory or pilot studies.


Ethics Statement:
This study was approved by the Institutional Review Board (IRB) at Oklahoma State University. All participants provided written informed consent.

Contact:
For questions or collaboration inquiries, contact Dr. Joseph Nuamah (jnuamah@okstate.edu).


By making this dataset publicly available, we aim to support reproducibility, interdisciplinary collaboration, and advancements in stress resilience research.