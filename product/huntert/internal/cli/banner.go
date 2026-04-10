package cli

import (
	"fmt"
	"os"
	"strings"
	"time"
)

const displayName = "HunterT"

var bannerVariants = []string{
	` _   _             _            _____
| | | |_   _ _ __ | |_ ___ _ __|_   _|
| |_| | | | | '_ \| __/ _ \ '__| | |
|  _  | |_| | | | | ||  __/ |    | |
|_| |_|\__,_|_| |_|\__\___|_|    |_|`,
	` _   _             _            _____
| | | | |_ _ __ ___| |_ ___ _ __|_   _|
| |_| | __| '__/ _ \ __/ _ \ '__| | |
|  _  | |_| | |  __/ ||  __/ |    | |
|_| |_|\__|_|  \___|\__\___|_|    |_|`,
	` _   _             _            _____
| |_| |_   _ _ __ | |_ ___ _ __ |_   _|
|  _  | | | | '_ \| __/ _ \ '__|  | |
| | | | |_| | | | | ||  __/ |     | |
\_| |_/\__,_|_| |_|\__\___|_|     |_|`,
}

func rootBanner() string {
	if strings.TrimSpace(os.Getenv("HUNTERT_NO_BANNER")) != "" {
		return ""
	}

	now := time.Now()
	variant := bannerVariants[now.YearDay()%len(bannerVariants)]
	tagline := bannerTagline(now)
	return fmt.Sprintf("%s\n%s v%s | %s | %s\n\n", variant, displayName, versionValue, tagline, backendMode+" + "+engineMode)
}

func bannerTagline(now time.Time) string {
	switch {
	case now.Hour() < 6:
		return "night crawl"
	case now.Hour() < 12:
		return "path hunt"
	case now.Hour() < 18:
		return "surface sweep"
	default:
		return "deep scan"
	}
}
