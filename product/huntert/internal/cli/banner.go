package cli

import (
	"fmt"
	"os"
	"strings"
	"time"
)

const displayName = "HunterT"

type bannerTheme struct {
	lineColors  []int
	metaColor   int
	borderColor int
	borderFill  string
	metaPrefix  string
}

var bannerVariants = [][]string{
	{
		`HH   HH UU   UU NN   NN TTTTTTT EEEEEEE RRRRRR  TTTTTTT`,
		`HH   HH UU   UU NNN  NN   TTT   EE      RR   RR   TTT  `,
		`HHHHHHH UU   UU NN N NN   TTT   EEEEE   RRRRRR    TTT  `,
		`HH   HH UU   UU NN  NNN   TTT   EE      RR  RR    TTT  `,
		`HH   HH  UUUUU  NN   NN   TTT   EEEEEEE RR   RR   TTT  `,
	},
	{
		`H   H U   U N   N TTTTT EEEEE RRRR  TTTTT`,
		`H   H U   U NN  N   T   E     R   R   T  `,
		`HHHHH U   U N N N   T   EEEE  RRRR    T  `,
		`H   H U   U N  NN   T   E     R  R    T  `,
		`H   H  UUU  N   N   T   EEEEE R   R   T  `,
	},
	{
		`##   ## ##   ## ###  ## ####### ####### ######  #######`,
		`##   ## ##   ## #### ##   ###   ##      ##   ##   ###  `,
		`####### ##   ## ## ####   ###   #####   ######    ###  `,
		`##   ## ##   ## ##  ###   ###   ##      ##  ##    ###  `,
		`##   ##  #####  ##   ##   ###   ####### ##   ##   ###  `,
	},
}

var bannerThemes = []bannerTheme{
	{
		lineColors:  []int{45, 51, 87, 123, 159},
		metaColor:   117,
		borderColor: 45,
		borderFill:  "=",
		metaPrefix:  "signal",
	},
	{
		lineColors:  []int{196, 202, 208, 214, 220},
		metaColor:   221,
		borderColor: 202,
		borderFill:  "~",
		metaPrefix:  "burn",
	},
	{
		lineColors:  []int{34, 40, 46, 82, 118},
		metaColor:   84,
		borderColor: 40,
		borderFill:  "#",
		metaPrefix:  "trace",
	},
	{
		lineColors:  []int{93, 99, 105, 141, 177},
		metaColor:   183,
		borderColor: 99,
		borderFill:  "-",
		metaPrefix:  "ghost",
	},
}

func rootBanner() string {
	if strings.TrimSpace(os.Getenv("HUNTERT_NO_BANNER")) != "" {
		return ""
	}

	now := time.Now()
	variant := bannerVariants[(now.YearDay()+now.Hour())%len(bannerVariants)]
	theme := bannerThemes[(now.YearDay()+int(now.Weekday())+now.Hour())%len(bannerThemes)]
	meta := fmt.Sprintf("%s | %s | %s + %s", bannerTagline(now), versionValue, backendMode, engineMode)
	return renderBanner(variant, theme, meta)
}

func renderBanner(lines []string, theme bannerTheme, meta string) string {
	width := len(meta)
	for _, line := range lines {
		if len(line) > width {
			width = len(line)
		}
	}

	border := strings.Repeat(theme.borderFill, width+4)
	metaLine := fmt.Sprintf("%s :: %s", strings.ToUpper(theme.metaPrefix), meta)

	var builder strings.Builder
	builder.WriteString(colorize(border, theme.borderColor, true))
	builder.WriteByte('\n')
	for index, line := range lines {
		padded := padRight(line, width)
		builder.WriteString(colorize("  "+padded, theme.lineColors[index%len(theme.lineColors)], true))
		builder.WriteByte('\n')
	}
	builder.WriteString(colorize("  "+padRight(metaLine, width), theme.metaColor, false))
	builder.WriteByte('\n')
	builder.WriteString(colorize(border, theme.borderColor, true))
	builder.WriteString("\n\n")
	return builder.String()
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

func colorize(value string, colorCode int, bold bool) string {
	if !bannerColorEnabled() {
		return value
	}

	prefix := fmt.Sprintf("\x1b[38;5;%dm", colorCode)
	if bold {
		prefix = fmt.Sprintf("\x1b[1;38;5;%dm", colorCode)
	}
	return prefix + value + "\x1b[0m"
}

func bannerColorEnabled() bool {
	if strings.TrimSpace(os.Getenv("NO_COLOR")) != "" {
		return false
	}
	term := strings.TrimSpace(os.Getenv("TERM"))
	if term == "" || term == "dumb" {
		return false
	}
	info, err := os.Stdout.Stat()
	if err != nil {
		return false
	}
	return info.Mode()&os.ModeCharDevice != 0
}

func padRight(value string, width int) string {
	if len(value) >= width {
		return value
	}
	return value + strings.Repeat(" ", width-len(value))
}
