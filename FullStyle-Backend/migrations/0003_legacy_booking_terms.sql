-- Preserve observed legacy terms once; repeat initialization no longer mutates data.
INSERT INTO booking_terms(appointment_id,duration,amount,currency)
SELECT a.id,d.duration,d.price,'COP'
FROM appointment a JOIN detail d ON d.site_id=a.site_id AND d.service_id=a.service_id
WHERE d.duration>0 AND d.price>=0
ON CONFLICT (appointment_id) DO NOTHING;
