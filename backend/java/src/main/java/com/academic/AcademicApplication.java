package com.academic;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AcademicApplication {

    public static void main(String[] args) {
        SpringApplication.run(AcademicApplication.class, args);
        System.out.println("============================================================");
        System.out.println("  Academic Performance Prediction System");
        System.out.println("  Running at: http://127.0.0.1:8080");
        System.out.println("============================================================");

        // Auto-open browser
        try {
            Runtime.getRuntime().exec("cmd /c start http://127.0.0.1:8080");
        } catch (Exception e) {
            System.out.println("  [INFO] Open http://127.0.0.1:8080 in your browser.");
        }
    }
}
