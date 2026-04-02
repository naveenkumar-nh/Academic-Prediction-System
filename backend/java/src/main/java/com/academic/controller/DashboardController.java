package com.academic.controller;

import com.academic.model.Student;
import com.academic.model.StudentAcademic;
import com.academic.model.PredictionHistory;
import com.academic.model.User;
import com.academic.repository.StudentAcademicRepository;
import com.academic.repository.StudentRepository;
import com.academic.repository.PredictionHistoryRepository;
import com.academic.repository.UserRepository;
import com.academic.service.PredictionService;
import jakarta.servlet.http.HttpSession;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import org.springframework.security.crypto.password.PasswordEncoder;

import com.lowagie.text.Document;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;

import java.awt.Color;
import java.io.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Controller
@RequestMapping("/dashboard")
public class DashboardController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private StudentRepository studentRepository;

    @Autowired
    private StudentAcademicRepository studentAcademicRepository;

    @Autowired
    private PredictionService predictionService;

    @Autowired
    private PredictionHistoryRepository predictionHistoryRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    // ============================================================
    // ADMIN DASHBOARD
    // ============================================================

    @GetMapping("/admin")
    public String adminDashboard(HttpSession session, Model model, RedirectAttributes redirectAttributes) {
        if (!"admin".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied. Admin only.");
            return "redirect:/";
        }

        List<User> staffList = userRepository.findByRoleOrderByCreatedAtDesc("staff");
        List<User> adminList = userRepository.findByRoleOrderByCreatedAtDesc("admin");
        List<Student> students = studentRepository.findAllByOrderByCreatedAtDesc();

        List<Map<String, Object>> studentData = new ArrayList<>();
        for (Student s : students) {
            Map<String, Object> item = new HashMap<>();
            item.put("student", s);
            item.put("academic", studentAcademicRepository.findByRegNo(s.getRegNo()).orElse(null));
            studentData.add(item);
        }

        model.addAttribute("staffList", staffList);
        model.addAttribute("totalStaff", staffList.size());
        model.addAttribute("adminList", adminList);
        model.addAttribute("totalAdmins", adminList.size());
        model.addAttribute("totalStudents", students.size());
        model.addAttribute("studentData", studentData);
        model.addAttribute("userId", session.getAttribute("user_id"));

        return "admin_dashboard";
    }

    @PostMapping("/admin/add-staff")
    public String addStaff(@RequestParam("username") String username, @RequestParam("password") String password,
            HttpSession session, RedirectAttributes redirectAttributes) {
        if (!"admin".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }
        if (username.trim().isEmpty() || password.isEmpty()) {
            redirectAttributes.addFlashAttribute("error", "Username and Password are required.");
            return "redirect:/dashboard/admin";
        }
        if (password.length() < 4) {
            redirectAttributes.addFlashAttribute("error", "Password must be at least 4 characters.");
            return "redirect:/dashboard/admin";
        }
        if (userRepository.existsByUsername(username.trim())) {
            redirectAttributes.addFlashAttribute("error", "Username already exists.");
            return "redirect:/dashboard/admin";
        }

        User staff = new User(username.trim(), "staff");
        staff.setPasswordHash(passwordEncoder.encode(password));
        userRepository.save(staff);

        redirectAttributes.addFlashAttribute("success", "Staff \"" + username.trim() + "\" added successfully!");
        return "redirect:/dashboard/admin";
    }

    @PostMapping("/admin/delete-staff/{staffId}")
    @Transactional
    public String deleteStaff(@PathVariable("staffId") Long staffId, HttpSession session,
            RedirectAttributes redirectAttributes) {
        if (!"admin".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        User staff = userRepository.findById(staffId).orElse(null);
        if (staff == null || !"staff".equals(staff.getRole())) {
            redirectAttributes.addFlashAttribute("error", "Cannot delete this user.");
            return "redirect:/dashboard/admin";
        }

        // Unlink students created by this staff
        List<Student> assignedStudents = studentRepository.findByCreatedByOrderByCreatedAtDesc(staff.getId());
        for (Student s : assignedStudents) {
            s.setCreatedBy(null);
            studentRepository.save(s);
        }

        userRepository.delete(staff);
        redirectAttributes.addFlashAttribute("success", "Staff \"" + staff.getUsername() + "\" deleted.");
        return "redirect:/dashboard/admin";
    }

    @PostMapping("/admin/add-admin")
    public String addAdmin(@RequestParam("username") String username, @RequestParam("password") String password,
            HttpSession session, RedirectAttributes redirectAttributes) {
        if (!"admin".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }
        if (username.trim().isEmpty() || password.isEmpty()) {
            redirectAttributes.addFlashAttribute("error", "Username and Password are required.");
            return "redirect:/dashboard/admin";
        }
        if (password.length() < 4) {
            redirectAttributes.addFlashAttribute("error", "Password must be at least 4 characters.");
            return "redirect:/dashboard/admin";
        }
        if (userRepository.existsByUsername(username.trim())) {
            redirectAttributes.addFlashAttribute("error", "Username already exists.");
            return "redirect:/dashboard/admin";
        }

        User admin = new User(username.trim(), "admin");
        admin.setPasswordHash(passwordEncoder.encode(password));
        userRepository.save(admin);

        redirectAttributes.addFlashAttribute("success", "Admin \"" + username.trim() + "\" added successfully!");
        return "redirect:/dashboard/admin";
    }

    @PostMapping("/admin/delete-admin/{adminId}")
    public String deleteAdmin(@PathVariable("adminId") Long adminId, HttpSession session,
            RedirectAttributes redirectAttributes) {
        if (!"admin".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        User admin = userRepository.findById(adminId).orElse(null);
        if (admin == null || !"admin".equals(admin.getRole())) {
            redirectAttributes.addFlashAttribute("error", "Cannot delete this user.");
            return "redirect:/dashboard/admin";
        }

        Long currentUserId = (Long) session.getAttribute("user_id");
        if (admin.getId().equals(currentUserId)) {
            redirectAttributes.addFlashAttribute("error", "You cannot delete your own account.");
            return "redirect:/dashboard/admin";
        }

        userRepository.delete(admin);
        redirectAttributes.addFlashAttribute("success", "Admin \"" + admin.getUsername() + "\" deleted.");
        return "redirect:/dashboard/admin";
    }

    // ============================================================
    // STAFF DASHBOARD
    // ============================================================

    @GetMapping("/staff")
    public String staffDashboard(HttpSession session, Model model, RedirectAttributes redirectAttributes) {
        if (!"staff".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied. Staff only.");
            return "redirect:/";
        }

        Long userId = (Long) session.getAttribute("user_id");
        List<Student> students = studentRepository.findByCreatedByOrderByCreatedAtDesc(userId);

        List<Map<String, Object>> studentData = new ArrayList<>();
        for (Student s : students) {
            Map<String, Object> item = new HashMap<>();
            item.put("student", s);
            item.put("academic", studentAcademicRepository.findByRegNo(s.getRegNo()).orElse(null));
            studentData.add(item);
        }

        model.addAttribute("studentData", studentData);
        model.addAttribute("totalStudents", students.size());

        return "staff_dashboard";
    }

    @PostMapping("/staff/add-student")
    public String addStudent(@RequestParam("reg_no") String reg_no, @RequestParam("name") String name,
            @RequestParam("dept") String dept, @RequestParam("year") int year,
            @RequestParam("password") String password,
            @RequestParam(name = "staff_id", required = false) Long staff_id,
            HttpSession session, RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        String redirectTo = "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";

        if (reg_no.trim().isEmpty() || name.trim().isEmpty() || dept.trim().isEmpty() || password.isEmpty()) {
            redirectAttributes.addFlashAttribute("error", "All fields are required.");
            return redirectTo;
        }
        if (studentRepository.existsByRegNo(reg_no.trim())) {
            redirectAttributes.addFlashAttribute("error", "Please enter a valid register number.");
            return redirectTo;
        }

        Long assignedTo;
        if ("admin".equals(role)) {
            if (staff_id == null) {
                redirectAttributes.addFlashAttribute("error", "Please select a staff member to assign this student.");
                return redirectTo;
            }
            User staff = userRepository.findById(staff_id).orElse(null);
            if (staff == null || !"staff".equals(staff.getRole())) {
                redirectAttributes.addFlashAttribute("error", "Invalid staff member selected.");
                return redirectTo;
            }
            assignedTo = staff.getId();
        } else {
            assignedTo = (Long) session.getAttribute("user_id");
        }

        Student student = new Student(reg_no.trim(), name.trim(), dept.trim(), year, assignedTo);
        student.setPasswordHash(passwordEncoder.encode(password));
        studentRepository.save(student);

        redirectAttributes.addFlashAttribute("success",
                "Student \"" + name.trim() + "\" (Reg: " + reg_no.trim() + ") added successfully!");
        return redirectTo;
    }

    @GetMapping("/staff/enter-marks/{regNo}")
    public String enterMarksForm(@PathVariable("regNo") String regNo, HttpSession session, Model model,
            RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            redirectAttributes.addFlashAttribute("error", "Student not found.");
            return "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        }

        StudentAcademic academic = studentAcademicRepository.findByRegNo(regNo).orElse(null);

        model.addAttribute("student", student);
        model.addAttribute("academic", academic);
        model.addAttribute("userRole", role);
        return "enter_marks";
    }

    @PostMapping("/staff/enter-marks/{regNo}")
    public String enterMarks(@PathVariable("regNo") String regNo,
            @RequestParam("internal_1") double internal_1, @RequestParam("internal_2") double internal_2,
            @RequestParam("internal_3") double internal_3, @RequestParam("assignment") double assignment,
            @RequestParam("prev_sem_gpa") double prev_sem_gpa,
            @RequestParam("study_hours_per_day") double study_hours_per_day,
            @RequestParam("attendance") double attendance,
            @RequestParam(name = "extra_activity", required = false, defaultValue = "no") String extra_activity,
            @RequestParam(name = "extra_activity_type", required = false) String extra_activity_type,
            HttpSession session, RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        String redirectTo = "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            redirectAttributes.addFlashAttribute("error", "Student not found.");
            return redirectTo;
        }

        StudentAcademic academic = studentAcademicRepository.findByRegNo(regNo).orElse(new StudentAcademic(regNo));
        academic.setInternal1(internal_1);
        academic.setInternal2(internal_2);
        academic.setInternal3(internal_3);
        academic.setAssignment(assignment);
        academic.setPrevSemGpa(prev_sem_gpa);
        academic.setStudyHoursPerDay(study_hours_per_day);
        academic.setAttendance(attendance);
        academic.setExtraActivity("yes".equals(extra_activity));
        academic.setExtraActivityType(extra_activity_type != null && !extra_activity_type.trim().isEmpty()
                ? extra_activity_type.trim()
                : null);

        studentAcademicRepository.save(academic);
        redirectAttributes.addFlashAttribute("success", "Marks saved for " + student.getName() + "!");
        return redirectTo;
    }

    @PostMapping("/staff/predict/{regNo}")
    public String runPrediction(@PathVariable("regNo") String regNo, HttpSession session,
            RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        String redirectTo = "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        StudentAcademic academic = studentAcademicRepository.findByRegNo(regNo).orElse(null);
        if (academic == null) {
            redirectAttributes.addFlashAttribute("error", "No academic records found. Enter marks first.");
            return redirectTo;
        }

        Map<String, Object> data = new HashMap<>();
        data.put("internal_1", academic.getInternal1());
        data.put("internal_2", academic.getInternal2());
        data.put("internal_3", academic.getInternal3());
        data.put("assignment", academic.getAssignment());
        data.put("prev_sem_gpa", academic.getPrevSemGpa());
        data.put("study_hours_per_day", academic.getStudyHoursPerDay());
        data.put("extra_activity", academic.getExtraActivity());
        data.put("attendance", academic.getAttendance());

        Map<String, Object> result = predictionService.predictResult(data);

        academic.setPredictionResult((String) result.get("prediction_result"));
        academic.setRiskLevel((String) result.get("risk_level"));
        studentAcademicRepository.save(academic);

        // Save prediction history
        PredictionHistory history = new PredictionHistory(
                regNo, academic.internalAvg(), academic.getPrevSemGpa(), academic.getAttendance(),
                (String) result.get("prediction_result"), (String) result.get("risk_level"),
                (String) result.get("grade"));
        predictionHistoryRepository.save(history);

        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        String studentName = student != null ? student.getName() : regNo;
        redirectAttributes.addFlashAttribute("success",
                "Prediction for " + studentName + ": " + result.get("prediction_result") +
                        " (Risk: " + result.get("risk_level") + ", Grade: " + result.get("grade") + ")");
        return redirectTo;
    }

    @PostMapping("/staff/delete-student/{regNo}")
    @Transactional
    public String deleteStudent(@PathVariable("regNo") String regNo, HttpSession session,
            RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        String redirectTo = "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            redirectAttributes.addFlashAttribute("error", "Student not found.");
            return redirectTo;
        }

        studentAcademicRepository.deleteByRegNo(regNo);
        studentRepository.delete(student);
        redirectAttributes.addFlashAttribute("success", "Student \"" + student.getName() + "\" deleted.");
        return redirectTo;
    }

    // ============================================================
    // EDIT STUDENT
    // ============================================================

    @GetMapping("/staff/edit-student/{regNo}")
    public String showEditStudent(@PathVariable("regNo") String regNo, HttpSession session, Model model,
            RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            redirectAttributes.addFlashAttribute("error", "Student not found.");
            return "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        }

        model.addAttribute("student", student);
        model.addAttribute("userRole", role);
        return "edit_student";
    }

    @PostMapping("/staff/edit-student/{regNo}")
    public String updateStudent(@PathVariable("regNo") String regNo,
            @RequestParam("name") String name, @RequestParam("dept") String dept, @RequestParam("year") int year,
            @RequestParam(name = "password", required = false) String password,
            HttpSession session, RedirectAttributes redirectAttributes) {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            redirectAttributes.addFlashAttribute("error", "Access denied.");
            return "redirect:/";
        }

        String redirectTo = "admin".equals(role) ? "redirect:/dashboard/admin" : "redirect:/dashboard/staff";
        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            redirectAttributes.addFlashAttribute("error", "Student not found.");
            return redirectTo;
        }

        student.setName(name.trim());
        student.setDept(dept);
        student.setYear(year);
        if (password != null && !password.trim().isEmpty()) {
            student.setPasswordHash(passwordEncoder.encode(password.trim()));
        }
        studentRepository.save(student);

        redirectAttributes.addFlashAttribute("success", "Student \"" + student.getName() + "\" updated successfully!");
        return redirectTo;
    }

    // ============================================================
    // CSV DOWNLOADS
    // ============================================================

    @GetMapping("/download-students")
    public void downloadStudents(HttpSession session, HttpServletResponse response) throws IOException {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            response.sendRedirect("/");
            return;
        }

        List<Student> students;
        if ("admin".equals(role)) {
            students = studentRepository.findAllByOrderByNameAsc();
        } else {
            Long userId = (Long) session.getAttribute("user_id");
            students = studentRepository.findByCreatedByOrderByNameAsc(userId);
        }

        StringBuilder csv = new StringBuilder();
        csv.append(
                "#,Reg No,Name,Department,Year,Internal 1,Internal 2,Internal 3,Assignment,Internal Avg,Prev Sem GPA,Study Hours/Day,Attendance %,Extra Activity,Result,Risk Level\n");

        int i = 1;
        for (Student s : students) {
            StudentAcademic a = studentAcademicRepository.findByRegNo(s.getRegNo()).orElse(null);
            if (a != null) {
                csv.append(String.format("%d,%s,%s,%s,%d,%.1f,%.1f,%.1f,%.1f,%.2f,%.1f,%.1f,%.1f,%s,%s,%s\n",
                        i++, s.getRegNo(), s.getName(), s.getDept(), s.getYear(),
                        a.getInternal1(), a.getInternal2(), a.getInternal3(),
                        a.getAssignment(), a.internalAvg(), a.getPrevSemGpa(),
                        a.getStudyHoursPerDay(), a.getAttendance(),
                        a.getExtraActivity() ? "Yes" : "No",
                        a.getPredictionResult() != null ? a.getPredictionResult() : "Pending",
                        a.getRiskLevel() != null ? a.getRiskLevel() : "-"));
            } else {
                csv.append(String.format("%d,%s,%s,%s,%d,-,-,-,-,-,-,-,-,-,Pending,-\n",
                        i++, s.getRegNo(), s.getName(), s.getDept(), s.getYear()));
            }
        }

        response.setContentType("text/csv");
        response.setHeader("Content-Disposition", "attachment; filename=student_details.csv");
        response.getWriter().write(csv.toString());
    }

    @GetMapping("/download-students/{riskLevel}")
    public void downloadStudentsByRisk(@PathVariable("riskLevel") String riskLevel,
            HttpSession session, HttpServletResponse response) throws IOException {
        String role = (String) session.getAttribute("user_role");
        if (!"staff".equals(role) && !"admin".equals(role)) {
            response.sendRedirect("/");
            return;
        }

        if (!"Low".equals(riskLevel) && !"Medium".equals(riskLevel) && !"High".equals(riskLevel)) {
            response.sendRedirect("admin".equals(role) ? "/dashboard/admin" : "/dashboard/staff");
            return;
        }

        List<Student> students;
        if ("admin".equals(role)) {
            students = studentRepository.findAllByOrderByNameAsc();
        } else {
            Long userId = (Long) session.getAttribute("user_id");
            students = studentRepository.findByCreatedByOrderByNameAsc(userId);
        }

        StringBuilder csv = new StringBuilder();
        csv.append(
                "#,Reg No,Name,Department,Year,Internal 1,Internal 2,Internal 3,Assignment,Internal Avg,Prev Sem GPA,Study Hours/Day,Attendance %,Extra Activity,Result,Risk Level\n");

        int count = 0;
        for (Student s : students) {
            StudentAcademic a = studentAcademicRepository.findByRegNo(s.getRegNo()).orElse(null);
            if (a != null && riskLevel.equals(a.getRiskLevel())) {
                count++;
                csv.append(String.format("%d,%s,%s,%s,%d,%.1f,%.1f,%.1f,%.1f,%.2f,%.1f,%.1f,%.1f,%s,%s,%s\n",
                        count, s.getRegNo(), s.getName(), s.getDept(), s.getYear(),
                        a.getInternal1(), a.getInternal2(), a.getInternal3(),
                        a.getAssignment(), a.internalAvg(), a.getPrevSemGpa(),
                        a.getStudyHoursPerDay(), a.getAttendance(),
                        a.getExtraActivity() ? "Yes" : "No",
                        a.getPredictionResult() != null ? a.getPredictionResult() : "Pending",
                        a.getRiskLevel() != null ? a.getRiskLevel() : "-"));
            }
        }

        response.setContentType("text/csv");
        response.setHeader("Content-Disposition",
                "attachment; filename=" + riskLevel.toLowerCase() + "_risk_students.csv");
        response.getWriter().write(csv.toString());
    }

    // ============================================================
    // STUDENT DASHBOARD
    // ============================================================

    @GetMapping("/student")
    public String studentDashboard(HttpSession session, Model model, RedirectAttributes redirectAttributes) {
        if (!"student".equals(session.getAttribute("user_role"))) {
            redirectAttributes.addFlashAttribute("error", "Access denied. Student only.");
            return "redirect:/";
        }

        String regNo = (String) session.getAttribute("student_reg_no");
        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        if (student == null) {
            return "redirect:/";
        }

        StudentAcademic academic = studentAcademicRepository.findByRegNo(regNo).orElse(null);

        Map<String, Object> prediction = null;
        List<String> suggestions = new ArrayList<>();
        if (academic != null && academic.getPredictionResult() != null) {
            Map<String, Object> data = new HashMap<>();
            data.put("internal_1", academic.getInternal1());
            data.put("internal_2", academic.getInternal2());
            data.put("internal_3", academic.getInternal3());
            data.put("assignment", academic.getAssignment());
            data.put("prev_sem_gpa", academic.getPrevSemGpa());
            data.put("study_hours_per_day", academic.getStudyHoursPerDay());
            data.put("extra_activity", academic.getExtraActivity());
            data.put("attendance", academic.getAttendance());
            prediction = predictionService.predictResult(data);
            @SuppressWarnings("unchecked")
            List<String> sug = (List<String>) prediction.get("suggestions");
            suggestions = sug;
        }

        // Subject-wise analysis
        List<Map<String, Object>> subjectWise = new ArrayList<>();
        if (academic != null) {
            subjectWise.add(Map.of("name", "Internal Test 1", "marks", academic.getInternal1(), "max", 100.0, "status",
                    academic.getInternal1() >= 40 ? "Pass" : "Fail"));
            subjectWise.add(Map.of("name", "Internal Test 2", "marks", academic.getInternal2(), "max", 100.0, "status",
                    academic.getInternal2() >= 40 ? "Pass" : "Fail"));
            subjectWise.add(Map.of("name", "Internal Test 3", "marks", academic.getInternal3(), "max", 100.0, "status",
                    academic.getInternal3() >= 40 ? "Pass" : "Fail"));
            subjectWise.add(Map.of("name", "Assignment", "marks", academic.getAssignment(), "max", 30.0, "status",
                    academic.getAssignment() >= 12 ? "Pass" : "Fail"));
        }

        // Prediction history
        List<PredictionHistory> history = predictionHistoryRepository.findByRegNoOrderByPredictedAtDesc(regNo);

        // Calculate performance score (0-100) for gauge
        double performanceScore = 0;
        double deptAvgScore = 0;
        if (academic != null) {
            double internalAvg = academic.internalAvg();
            double score = 0;
            score += (internalAvg / 100.0) * 35;
            score += (academic.getPrevSemGpa() / 10.0) * 25;
            score += (academic.getAttendance() / 100.0) * 20;
            score += (Math.min(academic.getStudyHoursPerDay(), 6) / 6.0) * 10;
            score += (academic.getAssignment() / 30.0) * 10;
            performanceScore = Math.round(Math.min(score, 100) * 10.0) / 10.0;

            // Department average
            List<Student> deptStudents = studentRepository.findByDept(student.getDept());
            double totalDeptScore = 0;
            int deptCount = 0;
            for (Student ds : deptStudents) {
                StudentAcademic da = studentAcademicRepository.findByRegNo(ds.getRegNo()).orElse(null);
                if (da != null) {
                    double dsScore = 0;
                    dsScore += (da.internalAvg() / 100.0) * 35;
                    dsScore += (da.getPrevSemGpa() / 10.0) * 25;
                    dsScore += (da.getAttendance() / 100.0) * 20;
                    dsScore += (Math.min(da.getStudyHoursPerDay(), 6) / 6.0) * 10;
                    dsScore += (da.getAssignment() / 30.0) * 10;
                    totalDeptScore += Math.min(dsScore, 100);
                    deptCount++;
                }
            }
            if (deptCount > 0) {
                deptAvgScore = Math.round((totalDeptScore / deptCount) * 10.0) / 10.0;
            }
        }

        model.addAttribute("student", student);
        model.addAttribute("academic", academic);
        model.addAttribute("prediction", prediction);
        model.addAttribute("suggestions", suggestions);
        model.addAttribute("subjectWise", subjectWise);
        model.addAttribute("predictionHistory", history);
        model.addAttribute("performanceScore", performanceScore);
        model.addAttribute("deptAvgScore", deptAvgScore);

        return "student_dashboard";
    }

    @GetMapping("/student/download-report")
    @SuppressWarnings("unchecked")
    public void downloadPrediction(HttpSession session, HttpServletResponse response) throws Exception {
        if (!"student".equals(session.getAttribute("user_role"))) {
            response.sendRedirect("/");
            return;
        }

        String regNo = (String) session.getAttribute("student_reg_no");
        Student student = studentRepository.findByRegNo(regNo).orElse(null);
        StudentAcademic academic = studentAcademicRepository.findByRegNo(regNo).orElse(null);

        if (student == null || academic == null || academic.getPredictionResult() == null) {
            response.sendRedirect("/dashboard/student");
            return;
        }

        Map<String, Object> data = new HashMap<>();
        data.put("internal_1", academic.getInternal1());
        data.put("internal_2", academic.getInternal2());
        data.put("internal_3", academic.getInternal3());
        data.put("assignment", academic.getAssignment());
        data.put("prev_sem_gpa", academic.getPrevSemGpa());
        data.put("study_hours_per_day", academic.getStudyHoursPerDay());
        data.put("extra_activity", academic.getExtraActivity());
        data.put("attendance", academic.getAttendance());
        Map<String, Object> prediction = predictionService.predictResult(data);

        // Build PDF using OpenPDF
        response.setContentType("application/pdf");
        response.setHeader("Content-Disposition",
                "attachment; filename=Prediction_Report_" + student.getRegNo() + ".pdf");

        Document document = new Document(PageSize.A4, 56, 56, 85, 56);
        PdfWriter.getInstance(document, response.getOutputStream());
        document.open();

        // Colors
        Color primaryColor = new Color(0x1a, 0x23, 0x7e);
        Color lightBg = new Color(0xe8, 0xea, 0xf6);
        Color grayText = new Color(0x55, 0x55, 0x55);
        Color greenColor = new Color(0x2e, 0x7d, 0x32);
        Color redColor = new Color(0xc6, 0x28, 0x28);
        Color orangeColor = new Color(0xef, 0x6c, 0x00);

        // Fonts
        Font titleFont = new Font(Font.HELVETICA, 20, Font.BOLD, primaryColor);
        Font subtitleFont = new Font(Font.HELVETICA, 11, Font.NORMAL, grayText);
        Font headingFont = new Font(Font.HELVETICA, 14, Font.BOLD, primaryColor);
        Font normalFont = new Font(Font.HELVETICA, 10, Font.NORMAL);
        Font boldFont = new Font(Font.HELVETICA, 10, Font.BOLD);
        Font resultFont = new Font(Font.HELVETICA, 18, Font.BOLD);

        // Title
        Paragraph title = new Paragraph("Academic Performance Prediction Report", titleFont);
        title.setAlignment(Element.ALIGN_CENTER);
        document.add(title);

        Paragraph subtitle = new Paragraph("Generated by Academic Prediction System", subtitleFont);
        subtitle.setAlignment(Element.ALIGN_CENTER);
        subtitle.setSpacingAfter(16);
        document.add(subtitle);

        // HR
        document.add(new Paragraph(" "));

        // Student Info
        Paragraph infoHeading = new Paragraph("Student Information", headingFont);
        infoHeading.setSpacingBefore(16);
        infoHeading.setSpacingAfter(8);
        document.add(infoHeading);

        PdfPTable infoTable = new PdfPTable(4);
        infoTable.setWidthPercentage(100);
        infoTable.setWidths(new float[] { 80, 150, 80, 150 });

        addInfoCell(infoTable, "Name", boldFont, lightBg);
        addInfoCell(infoTable, student.getName(), normalFont, Color.WHITE);
        addInfoCell(infoTable, "Register No", boldFont, lightBg);
        addInfoCell(infoTable, student.getRegNo(), normalFont, Color.WHITE);
        addInfoCell(infoTable, "Department", boldFont, lightBg);
        addInfoCell(infoTable, student.getDept(), normalFont, Color.WHITE);
        addInfoCell(infoTable, "Year", boldFont, lightBg);
        addInfoCell(infoTable, String.valueOf(student.getYear()), normalFont, Color.WHITE);

        document.add(infoTable);
        document.add(new Paragraph(" "));

        // Academic Details
        Paragraph marksHeading = new Paragraph("Academic Details", headingFont);
        marksHeading.setSpacingBefore(16);
        marksHeading.setSpacingAfter(8);
        document.add(marksHeading);

        PdfPTable marksTable = new PdfPTable(2);
        marksTable.setWidthPercentage(100);
        marksTable.setWidths(new float[] { 230, 230 });

        // Header
        addHeaderCell(marksTable, "Subject", primaryColor);
        addHeaderCell(marksTable, "Marks", primaryColor);

        // Rows
        String[][] marksData = {
                { "Internal Test 1", String.valueOf(academic.getInternal1()) },
                { "Internal Test 2", String.valueOf(academic.getInternal2()) },
                { "Internal Test 3", String.valueOf(academic.getInternal3()) },
                { "Assignment", String.valueOf(academic.getAssignment()) },
                { "Internal Average", String.valueOf(academic.internalAvg()) },
                { "Previous Sem GPA", String.valueOf(academic.getPrevSemGpa()) },
                { "Study Hours/Day", String.valueOf(academic.getStudyHoursPerDay()) },
                { "Attendance %", String.valueOf(academic.getAttendance()) },
                { "Extra Activity", academic.getExtraActivity() ? "Yes" : "No" }
        };

        for (int i = 0; i < marksData.length; i++) {
            Color bg = (i == 4) ? lightBg : Color.WHITE; // Highlight Internal Average row
            Font f = (i == 4) ? boldFont : normalFont;
            addInfoCell(marksTable, marksData[i][0], f, bg);
            PdfPCell cell = new PdfPCell(new Phrase(marksData[i][1], normalFont));
            cell.setBackgroundColor(bg);
            cell.setHorizontalAlignment(Element.ALIGN_CENTER);
            cell.setPadding(7);
            marksTable.addCell(cell);
        }

        document.add(marksTable);
        document.add(new Paragraph(" "));

        // Prediction Result
        Paragraph resultHeading = new Paragraph("Prediction Result", headingFont);
        resultHeading.setSpacingBefore(16);
        resultHeading.setSpacingAfter(8);
        document.add(resultHeading);

        PdfPTable resultTable = new PdfPTable(3);
        resultTable.setWidthPercentage(100);

        addHeaderCell(resultTable, "Prediction", primaryColor);
        addHeaderCell(resultTable, "Grade", primaryColor);
        addHeaderCell(resultTable, "Risk Level", primaryColor);

        String predResult = (String) prediction.get("prediction_result");
        String grade = (String) prediction.get("grade");
        String risk = (String) prediction.get("risk_level");

        Color resultColor = "Pass".equals(predResult) ? greenColor : redColor;
        Color riskColor = "Low".equals(risk) ? greenColor : ("Medium".equals(risk) ? orangeColor : redColor);

        resultFont.setColor(resultColor);
        PdfPCell c1 = new PdfPCell(new Phrase(predResult, resultFont));
        c1.setHorizontalAlignment(Element.ALIGN_CENTER);
        c1.setPadding(10);
        resultTable.addCell(c1);

        Font gradeFont = new Font(Font.HELVETICA, 18, Font.BOLD);
        PdfPCell c2 = new PdfPCell(new Phrase(grade, gradeFont));
        c2.setHorizontalAlignment(Element.ALIGN_CENTER);
        c2.setPadding(10);
        resultTable.addCell(c2);

        Font riskFont = new Font(Font.HELVETICA, 18, Font.BOLD, riskColor);
        PdfPCell c3 = new PdfPCell(new Phrase(risk, riskFont));
        c3.setHorizontalAlignment(Element.ALIGN_CENTER);
        c3.setPadding(10);
        resultTable.addCell(c3);

        document.add(resultTable);
        document.add(new Paragraph(" "));

        // Subject-wise Report
        Paragraph subjectHeading = new Paragraph("Subject-wise Performance", headingFont);
        subjectHeading.setSpacingBefore(16);
        subjectHeading.setSpacingAfter(8);
        document.add(subjectHeading);

        PdfPTable subjectTable = new PdfPTable(4);
        subjectTable.setWidthPercentage(100);
        addHeaderCell(subjectTable, "Subject", primaryColor);
        addHeaderCell(subjectTable, "Marks", primaryColor);
        addHeaderCell(subjectTable, "Max Marks", primaryColor);
        addHeaderCell(subjectTable, "Status", primaryColor);

        String[][] subjects = {
                { "Internal Test 1", String.valueOf(academic.getInternal1()), "100",
                        academic.getInternal1() >= 40 ? "Pass" : "Fail" },
                { "Internal Test 2", String.valueOf(academic.getInternal2()), "100",
                        academic.getInternal2() >= 40 ? "Pass" : "Fail" },
                { "Internal Test 3", String.valueOf(academic.getInternal3()), "100",
                        academic.getInternal3() >= 40 ? "Pass" : "Fail" },
                { "Assignment", String.valueOf(academic.getAssignment()), "30",
                        academic.getAssignment() >= 12 ? "Pass" : "Fail" }
        };

        for (String[] row : subjects) {
            addInfoCell(subjectTable, row[0], normalFont, Color.WHITE);
            PdfPCell mc = new PdfPCell(new Phrase(row[1], normalFont));
            mc.setHorizontalAlignment(Element.ALIGN_CENTER);
            mc.setPadding(7);
            subjectTable.addCell(mc);
            PdfPCell mxc = new PdfPCell(new Phrase(row[2], normalFont));
            mxc.setHorizontalAlignment(Element.ALIGN_CENTER);
            mxc.setPadding(7);
            subjectTable.addCell(mxc);
            Font statusFont = new Font(Font.HELVETICA, 10, Font.BOLD, "Pass".equals(row[3]) ? greenColor : redColor);
            PdfPCell sc = new PdfPCell(new Phrase(row[3], statusFont));
            sc.setHorizontalAlignment(Element.ALIGN_CENTER);
            sc.setPadding(7);
            subjectTable.addCell(sc);
        }

        document.add(subjectTable);
        document.add(new Paragraph(" "));

        // Suggestions
        List<String> suggestions = (List<String>) prediction.get("suggestions");
        if (suggestions != null && !suggestions.isEmpty()) {
            Paragraph sugHeading = new Paragraph("Suggestions for Improvement", headingFont);
            sugHeading.setSpacingBefore(16);
            sugHeading.setSpacingAfter(8);
            document.add(sugHeading);

            for (int i = 0; i < suggestions.size(); i++) {
                Paragraph p = new Paragraph((i + 1) + ". " + suggestions.get(i), normalFont);
                p.setSpacingAfter(4);
                document.add(p);
            }
        }

        // Footer
        document.add(new Paragraph(" "));
        Font footerFont = new Font(Font.HELVETICA, 8, Font.NORMAL, new Color(0x99, 0x99, 0x99));
        Paragraph footer1 = new Paragraph(
                "Generated on " + LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd MMMM yyyy, hh:mm a")),
                footerFont);
        footer1.setAlignment(Element.ALIGN_CENTER);
        document.add(footer1);

        Paragraph footer2 = new Paragraph(
                "Academic Performance Prediction System — Confidential", footerFont);
        footer2.setAlignment(Element.ALIGN_CENTER);
        document.add(footer2);

        document.close();
    }

    // PDF helper methods
    private void addInfoCell(PdfPTable table, String text, Font font, Color bgColor) {
        PdfPCell cell = new PdfPCell(new Phrase(text, font));
        cell.setBackgroundColor(bgColor);
        cell.setPadding(8);
        cell.setBorderColor(new Color(0xcc, 0xcc, 0xcc));
        cell.setBorderWidth(0.5f);
        table.addCell(cell);
    }

    private void addHeaderCell(PdfPTable table, String text, Color bgColor) {
        Font headerFont = new Font(Font.HELVETICA, 11, Font.BOLD, Color.WHITE);
        PdfPCell cell = new PdfPCell(new Phrase(text, headerFont));
        cell.setBackgroundColor(bgColor);
        cell.setHorizontalAlignment(Element.ALIGN_CENTER);
        cell.setPadding(10);
        cell.setBorderColor(new Color(0xcc, 0xcc, 0xcc));
        cell.setBorderWidth(0.5f);
        table.addCell(cell);
    }
}
