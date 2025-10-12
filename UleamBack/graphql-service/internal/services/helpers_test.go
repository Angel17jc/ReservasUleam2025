package services

import "testing"

func TestPqStringArray(t *testing.T) {
	val := pqStringArray([]string{"Aprobada", "Pendiente"}).(string)
	if val != `{"Aprobada","Pendiente"}` {
		t.Fatalf("unexpected pqStringArray: %s", val)
	}
}

func TestPqIntArray(t *testing.T) {
	val := pqIntArray([]int{1, 2, 3}).(string)
	if val != "{1,2,3}" {
		t.Fatalf("unexpected pqIntArray: %s", val)
	}
}
