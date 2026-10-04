package com.gcky.durginoutsystem;

import com.gcky.durginoutsystem.exception.BusinessException;
import com.gcky.durginoutsystem.service.DatabaseBackupService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class DatabaseBackupServiceTest {

    @TempDir
    Path tempDirectory;

    @Test
    void returnsLatestSqlBackup() throws Exception {
        Path older = Files.writeString(tempDirectory.resolve("pharmacy_db_2026-10-03_00-00-00.sql"), "old");
        Path latest = Files.writeString(tempDirectory.resolve("pharmacy_db_2026-10-04_00-00-00.sql"), "new");
        Files.setLastModifiedTime(older, FileTime.from(Instant.parse("2026-10-03T00:00:00Z")));
        Files.setLastModifiedTime(latest, FileTime.from(Instant.parse("2026-10-04T00:00:00Z")));

        DatabaseBackupService service = new DatabaseBackupService(tempDirectory.toString());

        assertEquals(latest, service.getLatestBackup());
    }

    @Test
    void rejectsMissingBackupDirectory() {
        DatabaseBackupService service = new DatabaseBackupService(
                tempDirectory.resolve("missing").toString());

        assertThrows(BusinessException.class, service::getLatestBackup);
    }
}
