package models

type User struct {
	ID           uint    `gorm:"primaryKey"`
	Name         string  `gorm:"not null"`
	Email        string  `gorm:"unique;not null"`
	Password     string  `gorm:"not null"`
	Active       bool    `gorm:"default:true"`
	AuthProvider string  `gorm:"default:'credentials'"`
	GoogleID     *string `gorm:"default:null"`

	//Manager *Manager `gorm:"foreignKey:ID"`
}

func (User) TableName() string {
	return "userr"
}
