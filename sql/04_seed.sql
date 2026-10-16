-- ============================================================
-- Sample data (5+ rows per table). Pump and field rows are the
-- exact sample data given in Set 59.
-- ============================================================

INSERT INTO irrigation_pump VALUES ('PMP-3310', 75.5, 1200, 'Diesel');
INSERT INTO irrigation_pump VALUES ('PMP-3320', 110.0, 1800, 'Electric');
INSERT INTO irrigation_pump VALUES ('PMP-3330', 60.0, 950, 'Electric');
INSERT INTO irrigation_pump VALUES ('PMP-3340', 75.5, 1250, 'Diesel');
INSERT INTO irrigation_pump VALUES ('PMP-3350', 150.0, 2500, 'Diesel');
INSERT INTO irrigation_pump VALUES ('PMP-3360', 45.0, 700, 'Electric');

INSERT INTO agricultural_field VALUES ('FLD-01', 'Almond Orchard', 120, 'Pivot-Line', 'PMP-3350');
INSERT INTO agricultural_field VALUES ('FLD-02', 'Wine Grapes', 45, 'Drip-System', 'PMP-3330');
INSERT INTO agricultural_field VALUES ('FLD-03', 'Alfalfa Crop', 200, 'Flood-Gate', 'PMP-3320');
INSERT INTO agricultural_field VALUES ('FLD-04', 'Sweet Corn', 80, 'Pivot-Line', 'PMP-3310');
INSERT INTO agricultural_field VALUES ('FLD-05', 'Almond Orchard', 95, 'Drip-System', 'PMP-3340');

INSERT INTO farm_owner VALUES ('OWN-01', 'Ramesh Kumar', '9840012345', 'Katpadi', 'ramesh.kumar@gmail.com');
INSERT INTO farm_owner VALUES ('OWN-02', 'Lakshmi Narayanan', '9876543210', 'Gudiyatham', 'lakshmi.n@gmail.com');
INSERT INTO farm_owner VALUES ('OWN-03', 'Suresh Babu', '9443321098', 'Arcot', 'suresh.babu@yahoo.com');
INSERT INTO farm_owner VALUES ('OWN-04', 'Meena Devi', '9790056789', 'Vaniyambadi', 'meena.devi@gmail.com');
INSERT INTO farm_owner VALUES ('OWN-05', 'Arjun Reddy', '9500123456', 'Ambur', 'arjun.reddy@outlook.com');

INSERT INTO field_lease VALUES (101, 'FLD-01', 'OWN-01', DATE '2024-04-01', DATE '2027-03-31', 360000);
INSERT INTO field_lease VALUES (102, 'FLD-02', 'OWN-02', DATE '2025-01-01', DATE '2026-12-31', 135000);
INSERT INTO field_lease VALUES (103, 'FLD-03', 'OWN-03', DATE '2023-06-01', DATE '2028-05-31', 400000);
INSERT INTO field_lease VALUES (104, 'FLD-04', 'OWN-04', DATE '2025-07-01', DATE '2027-06-30', 160000);
INSERT INTO field_lease VALUES (105, 'FLD-05', 'OWN-01', DATE '2024-10-01', DATE '2027-09-30', 285000);

INSERT INTO technician VALUES ('T01', 'Karthik S', 'Diesel Engine', '9001100011', DATE '2019-03-15', 550);
INSERT INTO technician VALUES ('T02', 'Priya M', 'Electric Motor', '9001100022', DATE '2021-08-01', 480);
INSERT INTO technician VALUES ('T03', 'Vignesh R', 'Hydraulics', '9001100033', DATE '2018-11-20', 600);
INSERT INTO technician VALUES ('T04', 'Anitha K', 'Electric Motor', '9001100044', DATE '2022-02-10', 450);
INSERT INTO technician VALUES ('T05', 'Rahul D', 'Diesel Engine', '9001100055', DATE '2023-06-05', 420);

INSERT INTO maintenance_log VALUES (1001, 'PMP-3350', 'T01', DATE '2026-01-12', 'Preventive', 3, 2500);
INSERT INTO maintenance_log VALUES (1002, 'PMP-3320', 'T02', DATE '2026-02-05', 'Repair', 5, 8200);
INSERT INTO maintenance_log VALUES (1003, 'PMP-3310', 'T05', DATE '2026-03-18', 'Overhaul', 8, 15500);
INSERT INTO maintenance_log VALUES (1004, 'PMP-3330', 'T04', DATE '2026-04-22', 'Preventive', 2, 1200);
INSERT INTO maintenance_log VALUES (1005, 'PMP-3350', 'T03', DATE '2026-06-09', 'Repair', 6, 9800);

INSERT INTO irrigation_schedule VALUES (5001, 'FLD-01', DATE '2026-07-01', 'Morning', 4, 576000);
INSERT INTO irrigation_schedule VALUES (5002, 'FLD-02', DATE '2026-07-01', 'Evening', 6, 162000);
INSERT INTO irrigation_schedule VALUES (5003, 'FLD-03', DATE '2026-07-02', 'Night', 5, 480000);
INSERT INTO irrigation_schedule VALUES (5004, 'FLD-04', DATE '2026-07-03', 'Morning', 3, 198000);
INSERT INTO irrigation_schedule VALUES (5005, 'FLD-05', DATE '2026-07-03', 'Evening', 4, 252000);

-- Default logins (passwords are hashed with PBKDF2-SHA256):
--   admin  / admin123   -> can insert, update, delete
--   viewer / viewer123  -> read-only
INSERT INTO app_user (username, password_hash, full_name, role) VALUES ('admin',
  'pbkdf2:sha256:1000000$mCqvESRufua2Clfj$46d06a25cbeef286fe0ef1d3e5f9d96012f6478d9583242dec895c8a3a80ba90',
  'Farm Administrator', 'admin');
INSERT INTO app_user (username, password_hash, full_name, role) VALUES ('viewer',
  'pbkdf2:sha256:1000000$ARqHTULT0D5AmmH0$573362083fd369a29a4bd8674dc6d9df8430e20213f9b5c0f5974ad98b0128f5',
  'Guest Viewer', 'viewer');

COMMIT;
