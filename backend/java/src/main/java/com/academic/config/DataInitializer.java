package com.academic.config;

import com.academic.model.User;
import com.academic.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class DataInitializer {

    @Bean
    CommandLineRunner initData(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        return args -> {
            // Create default admin account if none exists
            if (!userRepository.existsByRole("admin")) {
                User admin = new User("admin", "admin");
                admin.setPasswordHash(passwordEncoder.encode("admin123"));
                userRepository.save(admin);
                System.out.println("  [INFO] Default admin created: admin / admin123");
            }
        };
    }
}
