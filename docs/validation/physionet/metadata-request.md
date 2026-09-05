# Draft request for PhysioNet acquisition metadata

**Draft only — not sent.** The release README names Dr. Joseph Nuamah as the contact. This request concerns [release 1.0.0](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/).

**Subject:** Channel mapping and export settings for your EEG–fNIRS PhysioNet dataset

Dear Dr. Nuamah,

I am a high-school student working on an internship project comparing subsets of EEG and fNIRS recordings. I am preparing to use your Neurophysiological Dataset of Stress Resilience During Human-Computer Interaction, version 1.0.0, for preliminary task-condition classification.

Could you share the MATLAB/Simulink acquisition and export scripts mentioned on the dataset page, or a table clarifying these details?

- The correspondence between CSV rows 34–65 and EEG electrodes. The numbered coordinate file and the electrode list in Methods use different sequences. Which sequence matches the exported rows, and were there participant-specific changes?
- For each optical row 2–33: source, detector, wavelength or HbO/HbR identity, and numerical unit. We need to know which streams belong to the same physical measurement channel.
- The EEG unit, scale, reference, and filters or other processing applied before export.
- The meaning of the optical-density and concentration values, including conversion parameters, baseline definition, and any invalid-value codes.
- Native EEG and fNIRS sampling rates, how the shared stored time grid was produced, and any known synchronization delay. Please also clarify coordinate units and axes if available.

To make the optical question concrete, we found the same conversion in all 35 released paired files. For the first group, row 18 = 0.0817802215 × row 2 − 0.0383920168 × row 3, and row 19 = −0.0297720054 × row 2 + 0.0566332307 × row 3; the other seven groups follow the same pattern. Its inverse is 14 × [[1.1596, 0.7861], [0.6096, 1.6745]], matching published coefficients for 850/760 nm inputs and HbO/HbR outputs. Can you confirm those identities, the meaning of the factor 14 and the actual saved input/output units, and which transmitter/receiver each group represents? We have retained these as conditional interpretations pending confirmation.

We have read the participant marker notes. p11 has six pulses at 248.848, 325.028, 688.160, 1044.704, 1404.708, and 1769.068 seconds, but no accompanying correction note. Which five identify the task starts? For p16, the note says recording stopped after 24 minutes, but the published time row ends at 1,260.652 seconds. Is there an explanation or corrected recording?

We want to avoid assigning unsupported sensor locations or units. Any original configuration files or clarification would be very helpful.

Thank you.
