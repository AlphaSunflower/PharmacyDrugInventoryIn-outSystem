# 药品增删操作卡顿优化实施计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 消除"添加药品"、"删除药品"、"购进登记"、"发药"等操作时的 UI 卡顿现象，让操作响应流畅。

**Architecture:** 问题分为两层：(1) 前端 PyQt6 使用同步 HTTP 请求阻塞 UI 主线程；(2) 后端 Spring Boot 存在冗余 DB 查询（N+1 问题、重复 SUM 聚合）。本方案从前端异步化入手（效果最显著、风险最低），再逐步优化后端 SQL。

**Tech Stack:** Python 3.11 + PyQt6 + requests | Java 17 + Spring Boot 3.5.9 + MyBatis-Plus + MySQL

---

## 根因诊断

经过代码审查，卡顿由以下 6 个问题叠加导致：

| # | 层级 | 问题 | 影响 |
|---|------|------|------|
| 1 | 前端 | **同步 HTTP 阻塞 UI 线程** — 所有 `api_client.post/get/delete()` 是同步 `requests` 调用，运行在 Qt 事件循环线程上，期间整个 UI 冻结 | **致命** — 每次操作冻结 0.5~2s |
| 2 | 后端 | **`updateDrugTotalStock` 在循环中逐药调用** — `dispense()` 和 `addPurchaseBatch()` 中对每个药品分别执行 SELECT SUM + UPDATE drugs | **严重** — 每个药品增加 2 次 DB 往返 |
| 3 | 后端 | **`getPurchases` 逐条查询批次** — 每笔购进记录通过 `selectById(batchId)` 单独查询 | **中等** — N+1 查询 |
| 4 | 后端 | **`getDrugs` 批量加载所有批次** — 单次查询拉取全部药品的所有批次，数据量大时慢 | **轻微** — 取决于数据量 |
| 5 | 前端 | **自动刷新轮询** — DispenseView 每 8s 刷新、MainWindow 每 5s 轮询通知，每次都是同步调用 | **中等** — 周期性卡顿 |
| 6 | 后端 | **操作日志同步写入** — `@Log` AOP 切面同步 INSERT 到 operation_logs | **轻微** — try-catch 不阻塞主流程，但增加 DB 开销 |

---

## 优化策略（按优先级）

### Strategy A: 前端异步化（第 1 优先级，效果最显著）
- 将 API 调用从同步改为异步，使用 `QThread` + worker 模式
- 改造 `api_client` 为线程安全的单例
- 所有视图的 `load_data()`、`add/delete` 操作通过后台线程执行，UI 立即响应

### Strategy B: 后端批量聚合（第 2 优先级）
- 合并 `updateDrugTotalStock` 调用
- 消除 `getPurchases` 的 N+1 查询
- 操作日志异步化

---

## Task 1: 创建异步 API Worker 基础设施

**Objective:** 建立 `QThread` + signal/slot 的基础设施，让所有 API 调用在后台线程执行

**Files:**
- Create: `client/utils/async_api.py`

**Step 1: 创建异步 API 请求 Worker**

```python
# client/utils/async_api.py
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import traceback
from utils.api_client import api_client

class ApiWorker(QObject):
    """在后台线程执行 API 请求，通过信号通知结果"""
    finished = pyqtSignal(object)  # emit (success: bool, data: dict, error_msg: str)
    
    def __init__(self, method: str, endpoint: str, data=None, params=None):
        super().__init__()
        self.method = method
        self.endpoint = endpoint
        self.data = data
        self.params = params
    
    def run(self):
        try:
            callable_method = getattr(api_client, self.method)
            if self.data is not None:
                res = callable_method(self.endpoint, data=self.data)
            elif self.params is not None:
                res = callable_method(self.endpoint, params=self.params)
            else:
                res = callable_method(self.endpoint)
            
            if res.status_code == 200:
                body = res.json()
                if body.get('code') == 200:
                    self.finished.emit((True, body.get('data'), ''))
                else:
                    self.finished.emit((False, None, body.get('message', '操作失败')))
            else:
                self.finished.emit((False, None, f'HTTP {res.status_code}'))
        except Exception as e:
            self.finished.emit((False, None, str(e)))


def run_async(parent, method, endpoint, data=None, params=None, on_success=None, on_error=None):
    """
    创建一个后台线程运行 API 调用，结果通过回调通知
    
    Args:
        parent: QWidget 父对象（管理生命周期）
        method: 'get' | 'post' | 'put' | 'delete' | 'patch'
        endpoint: '/drugs' 等
        data: request body (dict)
        params: URL query params (dict)
        on_success: callable(data) — 成功回调
        on_error: callable(error_msg) — 失败回调
    """
    thread = QThread(parent)
    worker = ApiWorker(method, endpoint, data, params)
    worker.moveToThread(thread)
    
    def handle_result(result):
        success, data, error_msg = result
        if success:
            if on_success:
                on_success(data)
        else:
            if on_error:
                on_error(error_msg)
        thread.quit()
    
    worker.finished.connect(handle_result)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
```

**Step 2: 验证文件创建**

Run: `ls -la client/utils/async_api.py`
Expected: 文件存在

**Step 3: Commit**

```bash
git add client/utils/async_api.py
git commit -m "feat: add async API worker for non-blocking Qt HTTP requests"
```

---

## Task 2: 改造 DrugManageView 为异步操作

**Objective:** 将药品管理的"新增"、"删除"、"加载列表"操作改为异步，消除 UI 卡顿

**Files:**
- Modify: `client/ui/pharmacist_views.py` — `DrugManageView` 类

**Step 1: 改造 `load_data()` 为异步**

在 `DrugManageView.load_data()` 中，将：

```python
def load_data(self):
    page = self.pagination.current_page
    size = self.pagination.page_size
    keyword = self.search_input.text()
    params = {"keyword": keyword, "page": page, "size": size}
    # ... min/max stock ...
    res = api_client.get("/drugs", params=params)
    if res.status_code == 200:
        data = res.json()
        if data['code'] == 200:
            self.drugs = data['data']['records']
            self.pagination.update_state(...)
            self.refresh_table()
```

替换为：

```python
from utils.async_api import run_async

def load_data(self):
    page = self.pagination.current_page
    size = self.pagination.page_size
    keyword = self.search_input.text()
    params = {"keyword": keyword, "page": page, "size": size}
    if self.min_stock_input.text().strip():
        params["minStock"] = self.min_stock_input.text().strip()
    if self.max_stock_input.text().strip():
        params["maxStock"] = self.max_stock_input.text().strip()
    
    def on_success(data):
        self.drugs = data['records']
        self.pagination.update_state(data['current'], data['pages'], data['total'])
        self.refresh_table()
    
    def on_error(msg):
        ModernMessageBox.critical(self, "错误", f"加载失败: {msg}")
    
    run_async(self, 'get', '/drugs', params=params, on_success=on_success, on_error=on_error)
```

**Step 2: 改造 `delete_drug()` 为异步**

将同步的 `api_client.delete()` 改为：

```python
def delete_drug(self, drug_id):
    reply = ModernMessageBox.question(self, "确认", "确定要删除该药品吗？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        def on_success(_data):
            ModernMessageBox.information(self, "成功", "删除成功")
            self.load_data()
        def on_error(msg):
            ModernMessageBox.critical(self, "失败", f"删除失败: {msg}")
        run_async(self, 'delete', f'/drugs/{drug_id}', on_success=on_success, on_error=on_error)
```

**Step 3: 改造 `show_drug_dialog` 中的 save() 为异步**

在 save() 函数中，将同步的 `api_client.post()` / `api_client.put()` 替换为 `run_async()`。

**Step 4: Commit**

```bash
git add client/ui/pharmacist_views.py
git commit -m "perf: async DrugManageView operations to prevent UI freeze"
```

---

## Task 3: 改造 PurchaseView 为异步操作

**Objective:** 将购进登记的"加载列表"和"提交批量购进"改为异步

**Files:**
- Modify: `client/ui/pharmacist_views.py` — `PurchaseView` 类

**Step 1: 改造 `load_purchases()` 为异步**

将 `api_client.get("/purchases", ...)` 替换为 `run_async(self, 'get', '/purchases', params=..., on_success=...)`。

**Step 2: 改造 `submit_batch_purchase()` 为异步**

将 `api_client.post("/purchases/batch", ...)` 替换为 `run_async(self, 'post', '/purchases/batch', data=..., on_success=...)`。

**Step 3: Commit**

```bash
git add client/ui/pharmacist_views.py
git commit -m "perf: async PurchaseView operations to prevent UI freeze"
```

---

## Task 4: 改造 DispenseView 为异步操作

**Objective:** 将发药页面的"加载列表"、"发药"、"退回"操作改为异步

**Files:**
- Modify: `client/ui/pharmacist_views.py` — `DispenseView` 类

**Step 1: 改造 `load_data()` 为异步（使用 `run_async`）**

**Step 2: 改造 `dispense()` 为异步**

```python
def dispense(self, visit_id):
    reply = ModernMessageBox.question(self, "确认", "确认库存充足并进行发药？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        def on_success(_data):
            ModernMessageBox.information(self, "成功", "发药成功")
            self.load_data()
            mw = self.window()
            if hasattr(mw, 'stock_changed'):
                mw.stock_changed.emit()
        def on_error(msg):
            ModernMessageBox.critical(self, "失败", f"操作失败: {msg}")
        run_async(self, 'post', f'/visits/{visit_id}/dispense', on_success=on_success, on_error=on_error)
```

**Step 3: 改造 `reject()` 为异步**

同理。

**Step 4: Commit**

```bash
git add client/ui/pharmacist_views.py
git commit -m "perf: async DispenseView operations to prevent UI freeze"
```

---

## Task 5: 改造 MainWindow 通知轮询为异步

**Objective:** 将 MainWindow 的 `_check_notifications()` 改为异步，避免周期性卡顿

**Files:**
- Modify: `client/ui/main_window.py`

**Step 1: 改造 `_check_notifications()`**

将 `api_client.get("/visits/notification-counts")` 替换为：

```python
from utils.async_api import run_async

def _check_notifications(self):
    role = api_client.user_role
    
    def on_success(data):
        pending = data.get('pendingCount', 0)
        returned = data.get('returnedCount', 0)
        if role in ('PHARMACIST', 'ROOT'):
            self._update_badge("待发药", pending)
            if pending > self._prev_pending:
                diff = pending - self._prev_pending
                self._show_toast(f"有 {diff} 条新处方待处理", ...)
        if role in ('DOCTOR', 'ROOT'):
            self._update_badge("就诊记录", returned)
            if returned > self._prev_returned:
                diff = returned - self._prev_returned
                self._show_toast(f"有 {diff} 条处方状态已更新", ...)
        self._prev_pending = pending
        self._prev_returned = returned
    
    run_async(self, 'get', '/visits/notification-counts', on_success=on_success)
```

**Step 2: Commit**

```bash
git add client/ui/main_window.py
git commit -m "perf: async notification polling to prevent periodic UI freeze"
```

---

## Task 6: 后端 — 消除 dispense() 中的 N+1 updateDrugTotalStock

**Objective:** 发药操作时，将 `updateDrugTotalStock` 合并为批量更新，减少 DB 往返

**Files:**
- Modify: `DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/service/DrugStockService.java`
- Modify: `DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/service/impl/VisitServiceImpl.java`

**Step 1: 在 DrugStockService 中添加批量更新方法**

```java
// DrugStockService.java
/** 批量重算药品总库存：一次查询 + 批量更新 */
@Transactional
public void updateDrugTotalStockBatch(List<Long> drugIds) {
    if (drugIds == null || drugIds.isEmpty()) return;
    
    // 1. 一次查询所有药品的批次 SUM
    QueryWrapper<DrugBatch> query = new QueryWrapper<>();
    query.in("drug_id", drugIds);
    query.select("drug_id", "IFNULL(SUM(stock_quantity), 0) as total");
    query.groupBy("drug_id");
    List<Map<String, Object>> results = drugBatchMapper.selectMaps(query);
    
    Map<Long, Integer> totalMap = new HashMap<>();
    for (Map<String, Object> row : results) {
        Long drugId = (Long) row.get("drug_id");
        int total = ((BigDecimal) row.get("total")).intValue();
        totalMap.put(drugId, total);
    }
    
    // 2. 批量更新 (MyBatis-Plus 的 updateBatchById 或者用 CASE WHEN)
    for (Long drugId : drugIds) {
        Drug drug = new Drug();
        drug.setId(drugId);
        drug.setStockQuantity(totalMap.getOrDefault(drugId, 0));
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.updateById(drug);
    }
}
```

**Step 2: 在 VisitServiceImpl.dispense() 中使用批量方法**

在 dispense() 方法中，将所有需要更新库存的 drugId 收集起来，循环结束后统一调用：

```java
// 收集所有需要更新总库存的 drugId
List<Long> affectedDrugIds = new ArrayList<>();
for (VisitDrug vd : visitDrugs) {
    // ... FIFO 扣减逻辑不变 ...
    affectedDrugIds.add(drug.getId());
}
// 统一批量更新总库存
drugStockService.updateDrugTotalStockBatch(affectedDrugIds);
```

**Step 3: Commit**

```bash
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/service/DrugStockService.java
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/service/impl/VisitServiceImpl.java
git commit -m "perf: batch drug stock sync in dispense to reduce DB round-trips"
```

---

## Task 7: 后端 — 消除 PurchaseController 中的 N+1 updateDrugTotalStock

**Objective:** 批量购进操作时，收集所有 drugId 统一更新总库存

**Files:**
- Modify: `DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/controller/PurchaseController.java`

**Step 1: 改造 addPurchaseBatch()**

将循环中的 `drugStockService.updateDrugTotalStock(drug.getId())` 移到循环外，收集 drugId 后统一调用 `updateDrugTotalStockBatch()`。

```java
List<Long> affectedDrugIds = new ArrayList<>();
for (PurchaseDetail purchase : purchases) {
    // ... 创建批次、保存明细、更新药品价格 ...
    if (drug != null) {
        affectedDrugIds.add(drug.getId());
    }
}
// 批量更新总库存
drugStockService.updateDrugTotalStockBatch(affectedDrugIds);
```

**Step 2: Commit**

```bash
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/controller/PurchaseController.java
git commit -m "perf: batch drug stock sync in purchase to reduce DB round-trips"
```

---

## Task 8: 后端 — 消除 getPurchases 的 N+1 批次查询

**Objective:** 购进记录列表页中，批次信息应批量加载而非逐条查询

**Files:**
- Modify: `DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/controller/PurchaseController.java`

**Step 1: 批量加载批次信息**

```java
// 在 getPurchases() 方法中，替换逐条 selectById 为批量加载：
List<Long> batchIds = list.stream()
    .map(PurchaseDetail::getBatchId)
    .filter(id -> id != null)
    .distinct()
    .collect(Collectors.toList());

Map<Long, DrugBatch> batchMap = batchIds.isEmpty() ? Collections.emptyMap() :
    drugBatchMapper.selectBatchIds(batchIds).stream()
        .collect(Collectors.toMap(DrugBatch::getId, b -> b));

// 然后在 map 中使用：
DrugBatch batch = batchMap.get(p.getBatchId());
map.put("manufacturer", batch != null ? batch.getManufacturer() : null);
```

**Step 2: Commit**

```bash
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/controller/PurchaseController.java
git commit -m "perf: batch-load batches in getPurchases to eliminate N+1 queries"
```

---

## Task 9: 后端 — 操作日志写入改为异步

**Objective:** 将 `@Log` AOP 中的 operation_logs INSERT 改为异步执行，减少请求响应延迟

**Files:**
- Modify: `DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/aspect/LogAspect.java`

**Step 1: 启用 Spring 异步**

检查或创建配置类启用 `@EnableAsync`：

```java
// 在 DurgInOutSystemApplication 或新建 Config 类上添加
@EnableAsync
@SpringBootApplication
public class DurgInOutSystemApplication { ... }
```

**Step 2: 在 OperationLogService.save() 方法上添加 @Async**

```java
// OperationLogServiceImpl.java
@Override
@Async
public void save(OperationLog operationLog) {
    this.baseMapper.insert(operationLog);
}
```

**Step 3: Commit**

```bash
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/DurgInOutSystemApplication.java
git add DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/service/impl/OperationLogServiceImpl.java
git commit -m "perf: async operation log writing to reduce request latency"
```

---

## 验证清单

- [ ] 启动后端 Spring Boot 应用
- [ ] 启动前端 PyQt6 客户端
- [ ] 在"药品管理"页 **新增药品** → 表单提交后 UI 不卡，成功提示正常弹出
- [ ] 在"药品管理"页 **删除药品** → 删除后 UI 不卡，列表即时刷新
- [ ] 在"药品购进"页 **提交购进记录** → 提交过程 UI 不卡
- [ ] 在"待发药"页 **发药操作** → 发药后 UI 不卡，库存即时更新
- [ ] 在"待发药"页 **退回操作** → 退回后 UI 不卡
- [ ] 定时刷新不再导致明显卡顿（8s/5s 轮询）

## 风险和注意事项

1. **QThread 线程安全** — `run_async` 中 `on_success`/`on_error` 回调在主线程执行（通过 Qt 的信号槽机制），可以安全操作 UI 控件
2. **线程对象生命周期** — 使用 `parent` 参数将 QThread 绑定到 QWidget，widget 销毁时自动清理子线程
3. **批量更新事务** — `updateDrugTotalStockBatch` 需要 `@Transactional` 确保数据一致性
4. **异步日志** — `@Async` 需要配置线程池，默认 SimpleAsyncTaskExecutor 在并发高时可能创建大量线程，建议后续配置自定义线程池

## 可选后续优化（超出本次范围）

- Task 5+6: 为 API 调用添加 loading 指示器（骨架屏/进度条）
- 使用 `QThreadPool` 替代 `QThread` 以限制并发数
- 前端实现请求去重（快速连续点击时的 debounce）
- 后端增加 Redis 缓存热点药品数据
- 数据库连接池调优（HikariCP 的 maximumPoolSize）
