# Zalo Chatlog: Feature engineering + prediction pipeline for out-of-stock and negative


## Usage

1. Copy the chatlog data to data/01_raw/chatlog.parquet

2. Contact me for models

3. Execute the whole pipeline for each day in a date range of your choice

```bash
# Example: execute for dates from 2024-02-12 to 2024-02-13
./get_dates.sh 2024-02-12 2024-02-13 | ./kedro_execute_days.sh 
```

Prediction outputs will be saved to `kedro_output`

## Some Business domain knowledge

Each message can come from:

* robot
* human agent
* user (the customer)

Each message can be categorized further as follows:

```
|--- robot
|    |---- request_human_support
|    |    |---- success
|    |    |---- failure
|    |
|    |---- text
|    |    |---- greeting (e.g., "Dạ em chào Anh/Chị, em có thể hỗ trợ gì cho mình ạ...")
|    |    |---- ask_phone_general (e.g., "Anh, chị vui lòng nhắn tin SỐ ĐIỆN THOẠI MUA HÀNG để KÍCH HOẠT ...")
|    |    |---- closing_time (e.g., "Nhà thuốc Long châu đã nhận được yêu cầu hỗ trợ từ Quý khách, nhưng rất tiếc...")
|    |    |---- hist_vax_empty (e.g., "Tiếc quá! Nhà mình chưa tiêm chủng tại Long Châu nên chưa có thông tin...")
|    |    |---- next_vax_empty (e.g., "Nhà mình hiện Chưa Có Lịch Hẹn Tiêm Chủng tiếp theo")
|    |    |----  menu_vax (e.g., "Anh/Chị vui lòng chọn thông tin cần tra cứu bên dưới:
|    |                                                    Lịch sử tiêm chủng
|    |                                                    Lịch tiêm tiếp theo")
|    |---- image
|         |---- ask_phone_vax (e.g., "Vaccine/NhapSDT.png")
|         |---- song_khoe (e.g., "CHĂM CHỈ TẬP LUYỆN")
|         |---- recommendation (e.g., "xem thêm sản phẩm", "Xem ngay sản phẩm" )
|         |---- his_vax (e.g., "Vaccine/LichSuTiemChung")
|         |---- vax_reminder (e.g., "SapDenLichHenTiemChung" )
|         |---- diem_hien_tai (e.g., "Banner/DacQuyen", "để đổi quà nhé ạ")
|         |---- ask_phone_bat_dau_tich_diem (e.g., "Banner/HDNhapSDT")
|         |---- moi_doi_diem (e.g.,"khuyen-mai/dquyen", "mời nhà mình", "0D.png", "QUÀ")
|         |---- moi_quan_tam (e.g., "PleaseFollow.jpg")
|         |---- dua_ma_qr (e.g., "Mình vui lòng đưa mã QR")
|
|--- human agent
|    |---- file (screenshots, etc.)
|    |---- text 
|         |---- confirm_order (e.g., "Người đặt ... Địa chỉ khách hàng...") 
|         |---- other text (depends on the actual conversation)
|
|--- user
     |---- payload (pressing buttons)
     |    |---- welcome_flow            
     |    |---- Diemcuatoi              
     |    |---- Muathuoc                
     |    |---- goodbye_unfollow        
     |    |---- Tiemchung               
     |    |---- MaQR                    
     |    |---- Lịch sử tiêm chủng      
     |    |---- Gui_diem                
     |    |---- Lịch hẹn tiêm tiếp theo 
     |    |---- gui_qrcode_khachhang    
     |    |---- Point_log               
     |    |---- etc.
     |
     |---- file (screenshots, etc)
     |---- sticker (zalo sticke)
     |---- user_send_location 
     |---- text
          |---- phone number
          |---- other text (depends on the actual conversation)
```


