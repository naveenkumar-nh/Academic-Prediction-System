package com.academic.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "prediction_history")
public class PredictionHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "reg_no", length = 50, nullable = false)
    private String regNo;

    @Column(name = "internal_avg")
    private Double internalAvg;

    @Column(name = "prev_sem_gpa")
    private Double prevSemGpa;

    @Column
    private Double attendance;

    @Column(name = "prediction_result", length = 20)
    private String predictionResult;

    @Column(name = "risk_level", length = 20)
    private String riskLevel;

    @Column(length = 10)
    private String grade;

    @Column(name = "predicted_at")
    private LocalDateTime predictedAt = LocalDateTime.now();

    // Constructors
    public PredictionHistory() {
    }

    public PredictionHistory(String regNo, Double internalAvg, Double prevSemGpa, Double attendance,
            String predictionResult, String riskLevel, String grade) {
        this.regNo = regNo;
        this.internalAvg = internalAvg;
        this.prevSemGpa = prevSemGpa;
        this.attendance = attendance;
        this.predictionResult = predictionResult;
        this.riskLevel = riskLevel;
        this.grade = grade;
        this.predictedAt = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getRegNo() {
        return regNo;
    }

    public void setRegNo(String regNo) {
        this.regNo = regNo;
    }

    public Double getInternalAvg() {
        return internalAvg;
    }

    public void setInternalAvg(Double internalAvg) {
        this.internalAvg = internalAvg;
    }

    public Double getPrevSemGpa() {
        return prevSemGpa;
    }

    public void setPrevSemGpa(Double prevSemGpa) {
        this.prevSemGpa = prevSemGpa;
    }

    public Double getAttendance() {
        return attendance;
    }

    public void setAttendance(Double attendance) {
        this.attendance = attendance;
    }

    public String getPredictionResult() {
        return predictionResult;
    }

    public void setPredictionResult(String predictionResult) {
        this.predictionResult = predictionResult;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getGrade() {
        return grade;
    }

    public void setGrade(String grade) {
        this.grade = grade;
    }

    public LocalDateTime getPredictedAt() {
        return predictedAt;
    }

    public void setPredictedAt(LocalDateTime predictedAt) {
        this.predictedAt = predictedAt;
    }
}
