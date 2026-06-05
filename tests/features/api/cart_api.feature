Feature: 購物車 API
  作為 API 客戶端
  我需要一致的回應格式與正確的 HTTP 狀態碼

  Background:
    Given API 應用已啟動

  Scenario: 獲取不存在的購物車
    Given 購物車服務回傳空結果
    When 客戶端請求 "GET" "/api/cart?user_id=unknown"
    Then 回應狀態碼應為 404
    And 回應欄位 "success" 應為 false
    And 回應欄位 "code" 應為 404
