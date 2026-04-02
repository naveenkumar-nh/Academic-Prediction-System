package com.academic.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "student_academics")
public class StudentAcademic {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "reg_no", length = 50, nullable = false)
    private String regNo;

    // Internal marks
    @Column(name = "internal_1", nullable = false)
    private Double internal1 = 0.0;

    @Column(name = "internal_2", nullable = false)
    private Double internal2 = 0.0;

    @Column(name = "internal_3", nullable = false)
    private Double internal3 = 0.0;

    @Column(nullable = false)
    private Double assignment = 0.0;

    // Previous performance
    @Column(name = "prev_sem_gpa", nullable = false)
    private Double prevSemGpa = 0.0;

    // Study habits
    @Column(name = "study_hours_per_day", nullable = false)
    private Double studyHoursPerDay = 0.0;

    // Extra activities
    @Column(name = "extra_activity", nullable = false)
    private Boolean extraActivity = false;

    @Column(name = "extra_activity_type", length = 100)
    private String extraActivityType;

    // Attendance
    @Column(nullable = false)
    private Double attendance = 0.0; // 0-100%

    // Prediction output
    @Column(name = "prediction_result", length = 20)
    private String predictionResult; // Pass / Fail

    @Column(name = "risk_level", length = 20)
    private String riskLevel; // Low / Medium / High

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    // Constructors
    public StudentAcademic() {}

    public StudentAcademic(String regNo) {
        this.regNo = regNo;
        this.createdAt = LocalDateTime.now();
    }

    // Calculate average of internal marks
    public Double internalAvg() {
        return Math.round((internal1 + internal2 + internal3) / 3.0 * 100.0) / 100.0;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getRegNo() { return regNo; }
    public void setRegNo(String regNo) { this.regNo = regNo; }

    public Double getInternal1() { return internal1; }
    public void setInternal1(Double internal1) { this.internal1 = internal1; }

    public Double getInternal2() { return internal2; }
    public void setInternal2(Double internal2) { this.internal2 = internal2; }

    public Double getInternal3() { return internal3; }
    public void setInternal3(Double internal3) { this.internal3 = internal3; }

    public Double getAssignment() { return assignment; }
    public void setAssignment(Double assignment) { this.assignment = assignment; }

    public Double getPrevSemGpa() { return prevSemGpa; }
    public void setPrevSemGpa(Double prevSemGpa) { this.prevSemGpa = prevSemGpa; }

    public Double getStudyHoursPerDay() { return studyHoursPerDay; }
    public void setStudyHoursPerDay(Double studyHoursPerDay) { this.studyHoursPerDay = studyHoursPerDay; }

    public Boolean getExtraActivity() { return extraActivity; }
    public void setExtraActivity(Boolean extraActivity) { this.extraActivity = extraActivity; }

    public String getExtraActivityType() { return extraActivityType; }
    public void setExtraActivityType(String extraActivityType) { this.extraActivityType = extraActivityType; }

    public Double getAttendance() { return attendance; }
    public void setAttendance(Double attendance) { this.attendance = attendance; }

    public String getPredictionResult() { return predictionResult; }
    public void setPredictionResult(String predictionResult) { this.predictionResult = predictionResult; }

    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
