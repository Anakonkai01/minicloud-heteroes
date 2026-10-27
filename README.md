# MiniCloud độc lập: hướng dẫn dựng và thực hành

Đây là bộ khung để tự học và làm bài **Cloud Computing – MyMiniCloud**. Bạn có thể chép nguyên thư mục này sang một máy khác và chạy MiniCloud **mà không cần repo, mô hình, GPU hay dữ liệu HeteroES**. HeteroES chỉ là hướng tích hợp tùy chọn về sau.

Bộ khung hiện **chưa được chạy thử trên Docker hoặc EC2**: Compose đã được kiểm tra cú pháp, nhưng chưa có bằng chứng các container khởi động và kết nối thành công. Hãy thực hiện từng bước, ghi lại kết quả thật và xử lý lỗi nếu gặp; chưa nên mô tả đây là bài đã nghiệm thu.

## 1. Bài tập yêu cầu gì?

Đề yêu cầu mô phỏng 9 loại server trên mạng Docker, dùng Compose, kiểm thử trên máy local và triển khai lên AWS EC2. Ngoài phần demo cơ bản, đề có các mục mở rộng như blog, API sinh viên, database, xác thực, object storage, DNS, monitoring, dashboard, proxy và load balancing. Các công nghệ trong đề là gợi ý; bộ khung này chọn PostgreSQL và CoreDNS thay cho ví dụ MariaDB và BIND.

| Vai trò | Service trong dự án | Việc cần minh chứng |
| --- | --- | --- |
| Web | `web` (Nginx) | Trang chủ, blog và nội dung tự viết |
| Application | `app` (Flask) | API JSON và kết nối database |
| Database | `db` (PostgreSQL) | Bảng sinh viên, truy vấn và dữ liệu bền |
| Identity | `auth` (Keycloak) | Đăng nhập, realm, user và kiểm tra token |
| Object storage | `storage` (MinIO) | Tạo bucket, upload và tải file |
| DNS | `dns` (CoreDNS) | Truy vấn các bản ghi nội bộ mô phỏng |
| Monitoring | `prometheus`, `node-exporter`, `web-exporter` | Target UP và metric hợp lệ |
| Dashboard | `grafana` | Biểu đồ từ Prometheus |
| Gateway | `proxy` (Nginx) | Định tuyến web và API; bổ sung load balancing |

`node-exporter` và `web-exporter` là thành phần phụ, nên Compose có 11 service cho 9 vai trò. Luồng chính:

```text
Trình duyệt -> proxy -> web tĩnh
                    -> app Flask -> PostgreSQL
                                 -> HeteroES health (tùy chọn, để sau)
Prometheus -> node-exporter, web-exporter -> Nginx stub_status
Grafana -> Prometheus
Keycloak, MinIO và CoreDNS: các bài thực hành riêng
```

Prometheus lấy metric Nginx qua exporter thay vì coi trang HTML là metric. Node exporter đang chạy trong container; cần kiểm chứng phạm vi số liệu trước khi kết luận đó là số liệu đầy đủ của máy host.

## 2. Chuẩn bị máy và chuyển dự án

1. Cài và khởi động Docker Desktop trên Windows/macOS, hoặc Docker Engine và plugin Docker Compose trên Linux. Docker phải có quyền chạy container. Trên Windows, Docker Desktop thường sử dụng WSL2; dùng Linux containers.
2. Cần kết nối Internet để tải image và thư viện khi build lần đầu. Chuẩn bị đủ dung lượng đĩa cho image, dữ liệu và log; hiện chưa đo được dung lượng cần thiết của toàn bộ bộ khung.
3. Chép **toàn bộ thư mục `minicloud-heteroes`** sang máy mới bằng USB, lưu trữ đám mây hoặc Git. Đừng chỉ chép README: cần cả `compose.yaml`, `.env.example`, `app/`, `web/`, `db/`, `dns/`, `proxy/`, `prometheus/` và `grafana/`. Nếu máy ẩn file bắt đầu bằng dấu chấm, vẫn phải chép `.env.example` và `.gitignore`.
4. Mở terminal tại thư mục đã chép. Các lệnh dưới đây chạy từ thư mục chứa `compose.yaml`; không cần thư mục HeteroES.

Trên Linux/macOS dùng Terminal; trên Windows có thể dùng PowerShell. Kiểm tra:

```bash
docker --version
docker compose version
docker info
```

Nếu `docker info` báo không kết nối được daemon, khởi động Docker Desktop/Engine và kiểm tra quyền Docker của tài khoản. Chỉ có lệnh `docker --version` thành công chưa chứng tỏ daemon dùng được.

## 3. Tạo cấu hình riêng

Trên Linux/macOS:

```bash
cp .env.example .env
```

Trên Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Mở `.env` bằng trình soạn thảo và thay cả bốn mật khẩu mẫu bằng các giá trị **khác nhau**, đủ mạnh, chỉ gồm chữ, số, `_` hoặc `-` để tránh lỗi URL và Compose. MinIO yêu cầu mật khẩu đủ dài; dùng ít nhất 16 ký tự cho mỗi mật khẩu. Giữ `HETEROES_HEALTH_URL=` trống khi chưa tích hợp. `.env` là dữ liệu riêng, không chia sẻ hoặc đưa vào Git; `.env.example` chỉ là mẫu.

Các tài khoản demo được khai báo trong `compose.yaml`: PostgreSQL dùng `minicloud`, Keycloak và Grafana dùng `admin`, MinIO dùng `minicloudadmin`; mật khẩu tương ứng đọc từ `.env`. Không dùng các giá trị mẫu để triển khai công khai.

## 4. Khởi động và kiểm tra tình trạng

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Lệnh đầu kiểm tra cấu hình Compose đã được nội suy; không chứng minh image tải được hay dịch vụ chạy đúng. Lần đầu `up` có thể mất thời gian tải image và build app; Keycloak cũng có thể khởi động chậm. Xem log nếu một service chưa chạy:

```bash
docker compose logs --tail=100
docker compose logs --tail=100 app
docker compose logs --tail=100 auth
```

Dùng `docker compose ps` để xem trạng thái cả 11 service. Lệnh thành công và container đang chạy vẫn cần được xác minh bằng các bước kiểm thử sau. Các cổng được bind vào `127.0.0.1`, chỉ truy cập từ chính máy chạy Docker.

## 5. Kiểm thử từng phần trên local

Các lệnh `curl` dưới đây dùng shell Linux/macOS. Trong PowerShell dùng `curl.exe` thay cho `curl`, hoặc mở URL trên trình duyệt. Sau mỗi bước, ghi kết quả và chụp ảnh minh chứng nếu cần; không ghi mật khẩu hoặc token vào báo cáo.

### 5.1 Web, API và proxy

Mở `http://127.0.0.1:18080/` và `http://127.0.0.1:18080/blog/`. Kiểm tra thêm:

```bash
curl -i http://127.0.0.1:18080/
curl -i http://127.0.0.1:18080/blog/
curl -s http://127.0.0.1:18080/api/hello
curl -s http://127.0.0.1:18080/api/student
curl -s http://127.0.0.1:18080/student/
curl -s http://127.0.0.1:18080/api/students-db
```

Kỳ vọng trang web trả HTTP 200; `/api/hello` trả JSON; hai đường sinh viên trả cùng danh sách 5 bản ghi mẫu; `/api/students-db` trả 3 dòng từ PostgreSQL. `proxy` chuyển `/api/hello` thành `/hello` ở app; route `/student/` cũng trỏ tới API `/student`. Dữ liệu tên sinh viên và trang blog hiện chỉ là mẫu để bạn thay bằng nội dung bài làm.

### 5.2 Database

```bash
docker compose exec db psql -U minicloud -d minicloud -c 'SELECT * FROM students;'
```

Bảng `students` và ba dòng mẫu được tạo từ `db/init.sql` khi PostgreSQL khởi tạo **volume mới**. Nếu sửa file SQL sau khi volume đã có dữ liệu, script không tự chạy lại; hãy áp dụng thay đổi SQL chủ động hoặc dùng volume thử mới. Dữ liệu trong database này là của MiniCloud, chưa phải database HeteroES.

### 5.3 Identity

Mở `http://127.0.0.1:18081` và đăng nhập quản trị Keycloak bằng user `admin` và `AUTH_PASSWORD`. Để hoàn thành phần mở rộng, tự tạo realm theo mã sinh viên, hai user và client; sau đó cấu hình một endpoint kiểm tra chữ ký, issuer và audience của access token rồi ghi minh chứng. **Bộ khung chưa có endpoint `/secure`, chưa kiểm tra token và chưa kết nối đăng nhập HeteroES.**

### 5.4 Object storage

Mở `http://127.0.0.1:19001`, đăng nhập MinIO bằng `minicloudadmin` và `STORAGE_PASSWORD`. Tạo bucket thử, upload một file không nhạy cảm và tải lại để đối chiếu. Nếu demo URL công khai theo đề, chỉ đặt public cho object/bucket thử mà bạn chủ động chọn. MinIO hiện chưa là nơi lưu recovery của HeteroES.

### 5.5 DNS và mạng

CoreDNS đang có hai bản ghi mẫu. Nếu máy có `dig`, chạy:

```bash
dig @127.0.0.1 -p 11053 web.cloud.local +short
dig @127.0.0.1 -p 11053 app-backend.cloud.local +short
```

Kỳ vọng lần lượt là `10.10.10.10` và `10.10.10.20`. Đây là **địa chỉ minh họa trong `dns/Corefile`**, không phải địa chỉ thực của container; truy vấn thành công không chứng minh có thể kết nối đến các IP này. Trên Windows, chạy `dig` từ môi trường có sẵn công cụ này; không nhầm `127.0.0.1` bên trong WSL với host Windows khi cấu hình mạng không cho phép kết nối.

Để kiểm tra tên service Docker từ container app:

```bash
docker compose exec app python -c "import socket; print(socket.gethostbyname('db')); print(socket.gethostbyname('web'))"
```

Docker DNS phục vụ tên service như `db` và `web`; CoreDNS demo chưa được cấu hình làm DNS mặc định cho container. Tự thêm và kiểm thử các bản ghi khác theo đề nếu cần.

### 5.6 Prometheus và Grafana

Mở `http://127.0.0.1:19090/targets`, chờ ít nhất một chu kỳ scrape và kiểm tra target `node` và `web` có trạng thái UP. Truy vấn thử `node_cpu_seconds_total` và `nginx_connections_active`. Target UP chỉ chứng minh Prometheus scrape thành công; vẫn cần xác minh ý nghĩa và phạm vi metric.

Mở `http://127.0.0.1:13000`, đăng nhập `admin` với `GRAFANA_PASSWORD`. Datasource Prometheus được khai báo trong `grafana/provisioning/datasources/`. Tạo dashboard cho CPU, RAM và network theo đề, kiểm tra query trả dữ liệu và lưu ảnh minh chứng. Dashboard chưa được tạo sẵn.

### 5.7 Lưu dữ liệu và dừng dự án

PostgreSQL, MinIO, Prometheus và Grafana dùng Docker volumes. Sau khi tạo dữ liệu thử, có thể kiểm tra lại sau restart:

```bash
docker compose restart
docker compose ps
```

Dừng riêng dự án:

```bash
docker compose down
```

Lệnh này giữ volumes. `docker compose down -v` sẽ xóa volumes của dự án và dữ liệu trong đó; chỉ dùng khi bạn chủ động muốn xóa. Không dùng `docker stop $(docker ps -q)` hoặc lệnh xóa mọi container trên máy, vì sẽ ảnh hưởng dự án khác.

## 6. Tiếp tục hoàn thành bài tập

1. Viết ba bài blog HTML có hình minh họa và liên kết về trang chính trong `web/blog/`; cập nhật danh sách bài. Thay dữ liệu mẫu bằng dữ liệu phù hợp.
2. Hoàn tất bài thực hành identity, object storage, DNS và Grafana ở mục 5. Chứng minh cả trường hợp thành công và lỗi phù hợp, chẳng hạn truy cập thiếu token bị từ chối, sau khi đã viết endpoint xác thực.
3. Dựng hai web instance có nội dung nhận diện khác nhau, cấu hình upstream Nginx round robin và kiểm tra nhiều request. Bộ khung hiện chỉ có một web instance nên **chưa hoàn thành load balancing**.
4. Build và push ít nhất một image tùy chỉnh lên Docker Hub của bạn; ghi tên image, tag và cách kéo image vào báo cáo. Việc build local không đồng nghĩa đã push.
5. Triển khai toàn cụm lên EC2 Ubuntu và kiểm thử qua public IP theo yêu cầu đề. Compose hiện chỉ bind localhost, nên không thể truy cập từ ngoài EC2 với cấu hình hiện tại. Trước khi công khai cần thiết kế ingress, security group và bảo vệ các trang quản trị; Keycloak `start-dev` và cấu hình mẫu là dành cho thử nghiệm. Không công khai database hay dashboard quản trị chỉ để tiện demo.
6. Viết báo cáo theo cấu trúc trong đề: mục tiêu, sơ đồ, cấu hình, ảnh và lệnh kiểm thử, đánh giá, đường dẫn image/video, cùng số mục mở rộng thực sự đã hoàn thành.

## 7. Tích hợp HeteroES về sau — không bắt buộc để dựng MiniCloud

HeteroES là hệ thống độc lập gồm backend CPU, web, coordinator và worker GPU. Ở snapshot `a2bf5ea0`, backend có identity, SQLite và filesystem recovery riêng. MiniCloud không tự biến Keycloak, PostgreSQL hay MinIO thành các backend tương ứng của HeteroES. Việc tích hợp đầy đủ phải dựa trên phiên bản HeteroES và hợp đồng của nó tại thời điểm thực hiện.

Khi sẵn sàng, dùng **một bản HeteroES riêng có phiên bản cố định**, cấu hình private directory, database và cổng riêng; không dùng chung state với lab đang hoạt động. Chỉ sau khi backend thử nghiệm đã chạy và app container có đường mạng đến backend, đặt `HETEROES_HEALTH_URL` thành URL health phù hợp, ví dụ `http://<host-ma-container-truy-cap-duoc>:<port>/api/v1/health`, rồi chạy `docker compose up -d app`. `localhost` trong container chỉ chính container đó; tên hoặc IP host tùy môi trường Docker. Không giả định kết nối host có sẵn trên mọi máy.

Gọi `http://127.0.0.1:18080/api/heteroes-health`: khi chưa cấu hình, API trả 503 `not configured`; sau khi cấu hình, API chỉ báo khả năng truy cập HTTP và mã trạng thái. Đây không chứng minh đăng nhập, lưu trữ, worker GPU hay chạy thí nghiệm hoạt động. URL do người vận hành kiểm soát; đừng mở adapter này ra Internet mà chưa xem xét giới hạn truy cập.

## 8. Khi gặp lỗi

- **Cổng đã dùng:** tìm service đang chiếm cổng, rồi đổi phần bên trái của mapping `127.0.0.1:HOST:CONTAINER` trong `compose.yaml`; giữ cổng container trừ khi hiểu cấu hình nội bộ. Cập nhật URL demo tương ứng.
- **App trả 503 database:** xem `docker compose ps`, `docker compose logs db` và `docker compose logs app`; kiểm tra mật khẩu, tình trạng database và truy vấn ở mục 5.2. Nếu đổi mật khẩu `.env` sau khi database đã khởi tạo, volume cũ không tự đổi mật khẩu database.
- **Không tải được image:** kiểm tra Internet, registry, quyền Docker và dung lượng. Không có cam kết chạy ngoại tuyến.
- **Prometheus target DOWN:** xem log `web-exporter`, `web` và `prometheus`; kiểm tra kết nối nội bộ và chờ chu kỳ scrape. `web` là Nginx thường, exporter mới cung cấp endpoint metric cho Prometheus.
- **Không nhớ cấu hình:** xem `compose.yaml`, các file cấu hình từng service và `docker compose logs --tail=100 <service>`. Tránh chia sẻ log chứa mật khẩu hoặc token.

Nguồn tham chiếu của công việc này là đề bài được cung cấp riêng. Các bước trên là hướng dẫn và kỳ vọng để bạn tự kiểm chứng, chưa phải kết quả chạy thực tế.
