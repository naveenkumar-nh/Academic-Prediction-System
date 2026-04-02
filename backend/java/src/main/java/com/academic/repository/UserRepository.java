package com.academic.repository;

import com.academic.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    Optional<User> findByUsernameAndRole(String username, String role);
    List<User> findByRoleOrderByCreatedAtDesc(String role);
    boolean existsByUsername(String username);
    boolean existsByRole(String role);
}
