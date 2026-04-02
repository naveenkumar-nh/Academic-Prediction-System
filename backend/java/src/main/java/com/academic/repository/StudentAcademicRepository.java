package com.academic.repository;

import com.academic.model.StudentAcademic;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface StudentAcademicRepository extends JpaRepository<StudentAcademic, Long> {
    Optional<StudentAcademic> findByRegNo(String regNo);

    void deleteByRegNo(String regNo);
}
