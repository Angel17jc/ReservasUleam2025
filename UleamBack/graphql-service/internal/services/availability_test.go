package services

import "testing"

func TestComputeLibreSlots(t *testing.T) {
	intervals := []interval{
		{Ini: "09:00", Fin: "10:00"},
		{Ini: "11:00", Fin: "12:00"},
	}
	libres := computeLibreSlots("08:00", "13:00", intervals)
	if len(libres) != 3 {
		t.Fatalf("expected 3 slots libres, got %d", len(libres))
	}
	if libres[0]["hora_inicio"] != "08:00" || libres[0]["hora_fin"] != "09:00" {
		t.Fatalf("unexpected first slot: %+v", libres[0])
	}
	if libres[1]["hora_inicio"] != "10:00" || libres[1]["hora_fin"] != "11:00" {
		t.Fatalf("unexpected second slot: %+v", libres[1])
	}
	if libres[2]["hora_inicio"] != "12:00" || libres[2]["hora_fin"] != "13:00" {
		t.Fatalf("unexpected third slot: %+v", libres[2])
	}
}
