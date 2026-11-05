package models

import (
	"time"
)

type Manager struct {
	ID                     uint   `gorm:"primaryKey"`
	Bankaccount            int    `gorm:"not null"`
	Accounttype            string `gorm:"not null"`
	Bankentity             string `gorm:"not null"`
	Subscriptionactive     bool   `gorm:"not null;default:false"`
	Subscriptiontype       string `gorm:"default:''"`
	Subscriptionstartdate  time.Time
	Subscriptionfinishdate time.Time
	//User                   User `gorm:"foreignKey:ID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE"`
}

func (Manager) TableName() string {
	return "manager"
}
