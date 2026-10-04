package com.gcky.durginoutsystem.service;

import com.gcky.durginoutsystem.exception.BusinessException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Comparator;
import java.util.Optional;
import java.util.stream.Stream;

@Service
public class DatabaseBackupService {

    private final Path backupDirectory;

    public DatabaseBackupService(@Value("${backup.directory:./backups}") String backupDirectory) {
        this.backupDirectory = Paths.get(backupDirectory).toAbsolutePath().normalize();
    }

    public Path getLatestBackup() {
        if (!Files.isDirectory(backupDirectory)) {
            throw new BusinessException("暂无可用数据库备份");
        }

        try (Stream<Path> files = Files.list(backupDirectory)) {
            Optional<Path> latest = files
                    .filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".sql"))
                    .max(Comparator.comparingLong(this::lastModified));
            return latest.orElseThrow(() -> new BusinessException("暂无可用数据库备份"));
        } catch (IOException e) {
            throw new UncheckedIOException("读取数据库备份目录失败", e);
        }
    }

    private long lastModified(Path path) {
        try {
            return Files.getLastModifiedTime(path).toMillis();
        } catch (IOException e) {
            return Long.MIN_VALUE;
        }
    }
}
