package models

// Client representa la tabla client en la base de datos
type Client struct {
	ID       uint    `json:"id" gorm:"primaryKey"`
	Calendar *string `json:"calendar" gorm:"-"`
	User     User    `json:"user" gorm:"-"`
}

// TableName especifica el nombre de la tabla en la base de datos
func (Client) TableName() string {
	return "client"
}
