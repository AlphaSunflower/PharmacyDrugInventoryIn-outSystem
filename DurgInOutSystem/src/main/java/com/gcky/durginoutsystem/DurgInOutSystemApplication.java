package com.gcky.durginoutsystem;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.gcky.durginoutsystem.mapper")
@EnableScheduling
public class DurgInOutSystemApplication {

    public static void main(String[] args) {
        SpringApplication.run(DurgInOutSystemApplication.class, args);
    }

}
