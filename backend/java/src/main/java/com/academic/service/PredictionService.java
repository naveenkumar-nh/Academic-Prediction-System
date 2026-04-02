package com.academic.service;

import org.springframework.stereotype.Service;
import java.util.*;

/**
 * Rule-Based Academic Performance Prediction
 *
 * Rules:
 * - If internal_avg < 40 OR prev_sem_gpa < 5 OR study_hours < 1 → High Risk,
 * Fail
 * - If internal_avg 40-59 AND study_hours 1-2 → Medium Risk, Pass
 * - If internal_avg >= 60 AND prev_sem_gpa >= 6 AND study_hours >= 2 → Low
 * Risk, Pass
 * - If extra_activity = Yes and marks are good → bonus level upgrade
 */
@Service
public class PredictionService {

    public Map<String, Object> predictResult(Map<String, Object> data) {
        double internal1 = toDouble(data.get("internal_1"));
        double internal2 = toDouble(data.get("internal_2"));
        double internal3 = toDouble(data.get("internal_3"));
        double internalAvg = (internal1 + internal2 + internal3) / 3.0;
        double prevSemGpa = toDouble(data.get("prev_sem_gpa"));
        double studyHours = toDouble(data.get("study_hours_per_day"));
        double assignment = toDouble(data.get("assignment"));
        boolean extraActivity = toBool(data.get("extra_activity"));
        double attendance = toDouble(data.get("attendance"));

        String riskLevel;
        String predictionResult;

        // Determine risk level and result
        if (internalAvg < 40 || prevSemGpa < 5 || studyHours < 1 || attendance < 50) {
            riskLevel = "High";
            predictionResult = "Fail";
        } else if (internalAvg >= 40 && internalAvg < 60 && studyHours >= 1 && studyHours <= 2) {
            riskLevel = "Medium";
            predictionResult = "Pass";
        } else if (internalAvg >= 60 && prevSemGpa >= 6 && studyHours >= 2) {
            riskLevel = "Low";
            predictionResult = "Pass";
        } else {
            // Default cases
            if (internalAvg >= 50 && prevSemGpa >= 5) {
                riskLevel = "Medium";
                predictionResult = "Pass";
            } else {
                riskLevel = "High";
                predictionResult = "Fail";
            }
        }

        // Bonus for extra activities (upgrade risk level if passing)
        if (extraActivity && "Pass".equals(predictionResult)) {
            if ("High".equals(riskLevel)) {
                riskLevel = "Medium";
            } else if ("Medium".equals(riskLevel)) {
                riskLevel = "Low";
            }
        }

        // Attendance penalty (if below 75%, increase risk)
        if (attendance < 75 && "Pass".equals(predictionResult)) {
            if ("Low".equals(riskLevel)) {
                riskLevel = "Medium";
            } else if ("Medium".equals(riskLevel)) {
                riskLevel = "High";
            }
        }

        // Grade calculation based on internal average
        String grade;
        if (internalAvg >= 90) {
            grade = "A+";
        } else if (internalAvg >= 80) {
            grade = "A";
        } else if (internalAvg >= 70) {
            grade = "B";
        } else if (internalAvg >= 60) {
            grade = "C";
        } else if (internalAvg >= 50) {
            grade = "D";
        } else {
            grade = "F";
        }

        // Generate suggestions
        List<String> suggestions = new ArrayList<>();
        if (internalAvg < 40) {
            suggestions.add("Focus on improving internal test scores. Consider extra tutoring.");
        } else if (internalAvg < 60) {
            suggestions.add("Your internal marks are average. Aim for consistent performance.");
        }

        if (prevSemGpa < 5) {
            suggestions.add("Previous semester GPA is low. Review past subjects thoroughly.");
        } else if (prevSemGpa < 6) {
            suggestions.add("Try to improve your GPA above 6.0 for better standing.");
        }

        if (studyHours < 1) {
            suggestions.add("Increase daily study hours to at least 2 hours.");
        } else if (studyHours < 2) {
            suggestions.add("Try to study at least 2-3 hours per day for best results.");
        }

        if (assignment < 15) {
            suggestions.add("Improve assignment completion and quality.");
        }

        if (!extraActivity) {
            suggestions.add("Consider participating in extra-curricular activities for holistic development.");
        }

        if (attendance < 50) {
            suggestions.add("Attendance is critically low. Attend classes regularly to avoid failing.");
        } else if (attendance < 75) {
            suggestions.add("Attendance is below 75%. Improve attendance to maintain eligibility.");
        } else if (attendance < 85) {
            suggestions.add("Try to maintain attendance above 85% for better performance.");
        }

        if (suggestions.isEmpty()) {
            suggestions.add("Great performance! Keep up the excellent work!");
        }

        Map<String, Object> result = new HashMap<>();
        result.put("prediction_result", predictionResult);
        result.put("risk_level", riskLevel);
        result.put("grade", grade);
        result.put("internal_avg", Math.round(internalAvg * 100.0) / 100.0);
        result.put("attendance", attendance);
        result.put("suggestions", suggestions);

        return result;
    }

    private double toDouble(Object val) {
        if (val == null)
            return 0.0;
        if (val instanceof Number)
            return ((Number) val).doubleValue();
        try {
            return Double.parseDouble(val.toString());
        } catch (Exception e) {
            return 0.0;
        }
    }

    private boolean toBool(Object val) {
        if (val == null)
            return false;
        if (val instanceof Boolean)
            return (Boolean) val;
        return "true".equalsIgnoreCase(val.toString()) || "yes".equalsIgnoreCase(val.toString());
    }
}
