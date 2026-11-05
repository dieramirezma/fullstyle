package utils

import (
	"regexp"
	"strings"
)

// IsValidEmail checks if the provided email is valid according to a simple regex pattern.
func IsValidEmail(email string) bool {
	const emailPattern = `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
	re := regexp.MustCompile(emailPattern)
	return re.MatchString(email)
}

// FormatString trims whitespace from the beginning and end of a string.
func FormatString(s string) string {
	return strings.TrimSpace(s)
}
