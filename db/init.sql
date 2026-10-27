CREATE TABLE students (
  id SERIAL PRIMARY KEY,
  student_id VARCHAR(10) NOT NULL,
  fullname VARCHAR(100) NOT NULL,
  dob DATE NOT NULL,
  major VARCHAR(50) NOT NULL
);
INSERT INTO students (student_id, fullname, dob, major) VALUES
  ('SV001', 'Sinh vien mau 1', '2004-01-01', 'CNTT'),
  ('SV002', 'Sinh vien mau 2', '2004-02-01', 'CNTT'),
  ('SV003', 'Sinh vien mau 3', '2004-03-01', 'CNTT');
