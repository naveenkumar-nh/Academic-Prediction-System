package com.academic.repository;

import com.academic.model.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface StudentRepository extends JpaRepository<Student, Long> {
    Optional<Student> findByRegNo(String regNo);

    boolean existsByRegNo(String regNo);

    List<Student> findByCreatedByOrderByCreatedAtDesc(Long createdBy);

    List<Student> findAllByOrderByCreatedAtDesc();

    List<Student> findAllByOrderByNameAsc();

    List<Student> findByCreatedByOrderByNameAsc(Long createdBy);

    List<Student> findByDept(String dept);
}
