package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type WebhookClient struct {
	baseURL string
	client  *http.Client
}

func NewWebhookClient(baseURL string) *WebhookClient {
	return &WebhookClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		client:  &http.Client{Timeout: 3 * time.Second},
	}
}

func (w *WebhookClient) SendStatsUpdate(payload map[string]interface{}) error {
	url := w.baseURL + "/api/webhooks/stats-update"
	body, _ := json.Marshal(payload)
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := w.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("webhook stats-update failed with status %d", resp.StatusCode)
	}
	return nil
}
