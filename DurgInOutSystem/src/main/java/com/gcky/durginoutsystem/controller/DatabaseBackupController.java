package com.gcky.durginoutsystem.controller;

import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.service.DatabaseBackupService;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@RequireRole("ADMIN")
@RestController
@RequestMapping("/api/v1/database-backups")
public class DatabaseBackupController {

    private final DatabaseBackupService backupService;

    public DatabaseBackupController(DatabaseBackupService backupService) {
        this.backupService = backupService;
    }

    @Log("下载数据库备份")
    @GetMapping("/latest")
    public ResponseEntity<Resource> downloadLatest() throws IOException {
        Path backup = backupService.getLatestBackup();
        Resource resource = new FileSystemResource(backup);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"" + backup.getFileName() + "\"")
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .contentLength(Files.size(backup))
                .body(resource);
    }
}
