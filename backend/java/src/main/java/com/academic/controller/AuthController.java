package com.academic.controller;

import com.academic.model.Student;
import com.academic.model.User;
import com.academic.repository.StudentRepository;
import com.academic.repository.UserRepository;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.Collections;

@Controller
public class AuthController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private StudentRepository studentRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @GetMapping("/")
    public String roleSelect(HttpSession session) {
        // If already authenticated, redirect to dashboard
        if (session.getAttribute("user_role") != null) {
            return redirectByRole(session);
        }
        return "role_select";
    }

    @GetMapping("/login/{role}")
    public String loginForm(@PathVariable("role") String role, Model model, HttpSession session) {
        if (!role.equals("admin") && !role.equals("staff") && !role.equals("student")) {
            return "redirect:/";
        }
        if (session.getAttribute("user_role") != null) {
            return redirectByRole(session);
        }
        model.addAttribute("role", role);
        return "login_form";
    }

    @PostMapping("/login/{role}")
    public String login(@PathVariable("role") String role,
            @RequestParam(name = "username", required = false) String username,
            @RequestParam(name = "reg_no", required = false) String reg_no,
            @RequestParam("password") String password,
            HttpSession session,
            Model model,
            RedirectAttributes redirectAttributes) {

        if (!role.equals("admin") && !role.equals("staff") && !role.equals("student")) {
            redirectAttributes.addFlashAttribute("error", "Invalid role selected.");
            return "redirect:/";
        }

        if (role.equals("student")) {
            // Student login with Register Number + Password
            if (reg_no == null || reg_no.trim().isEmpty() || password.isEmpty()) {
                redirectAttributes.addFlashAttribute("error", "Please enter Register Number and Password.");
                return "redirect:/login/student";
            }

            Student student = studentRepository.findByRegNo(reg_no.trim()).orElse(null);
            if (student != null && passwordEncoder.matches(password, student.getPasswordHash())) {
                // Set session
                session.setAttribute("user_type", "student");
                session.setAttribute("user_role", "student");
                session.setAttribute("user_id", student.getId());
                session.setAttribute("user_name", student.getName());
                session.setAttribute("student_reg_no", student.getRegNo());

                // Set Spring Security context
                UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                        student.getRegNo(), null,
                        Collections.singletonList(new SimpleGrantedAuthority("ROLE_STUDENT")));
                SecurityContextHolder.getContext().setAuthentication(auth);

                redirectAttributes.addFlashAttribute("success", "Welcome, " + student.getName() + "!");
                return "redirect:/dashboard/student";
            } else {
                redirectAttributes.addFlashAttribute("error", "Invalid Register Number or Password.");
                return "redirect:/login/student";
            }
        } else {
            // Admin/Staff login with Username + Password
            if (username == null || username.trim().isEmpty() || password.isEmpty()) {
                redirectAttributes.addFlashAttribute("error", "Please enter Username and Password.");
                return "redirect:/login/" + role;
            }

            User user = userRepository.findByUsernameAndRole(username.trim(), role).orElse(null);
            if (user != null && passwordEncoder.matches(password, user.getPasswordHash())) {
                // Set session
                session.setAttribute("user_type", "user");
                session.setAttribute("user_role", role);
                session.setAttribute("user_id", user.getId());
                session.setAttribute("user_name", user.getUsername());

                // Set Spring Security context
                String authority = "ROLE_" + role.toUpperCase();
                UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                        user.getUsername(), null,
                        Collections.singletonList(new SimpleGrantedAuthority(authority)));
                SecurityContextHolder.getContext().setAuthentication(auth);

                redirectAttributes.addFlashAttribute("success", "Welcome, " + user.getUsername() + "!");
                if (role.equals("admin")) {
                    return "redirect:/dashboard/admin";
                } else {
                    return "redirect:/dashboard/staff";
                }
            } else {
                redirectAttributes.addFlashAttribute("error", "Invalid Username or Password.");
                return "redirect:/login/" + role;
            }
        }
    }

    @GetMapping("/logout")
    public String logout(HttpSession session, RedirectAttributes redirectAttributes) {
        session.invalidate();
        SecurityContextHolder.clearContext();
        redirectAttributes.addFlashAttribute("success", "You have been logged out.");
        return "redirect:/";
    }

    private String redirectByRole(HttpSession session) {
        String role = (String) session.getAttribute("user_role");
        if ("admin".equals(role))
            return "redirect:/dashboard/admin";
        if ("staff".equals(role))
            return "redirect:/dashboard/staff";
        if ("student".equals(role))
            return "redirect:/dashboard/student";
        return "redirect:/";
    }
}
