package services

import (
	"encoding/json"
	"fmt"
	"strconv"
)

func ToInt(val interface{}) (int, error) {
	switch v := val.(type) {
	case float64:
		return int(v), nil
	case string:
		return strconv.Atoi(v)
	case json.Number:
		return strconv.Atoi(v.String())
	default:
		return 0, fmt.Errorf("unknown type")
	}
}
