#!/bin/bash
#
# CV-RAG Sync Script
# Synkroniserer CVer fra Flowcase og re-indekserer automatisk
#
# Usage:
#   ./sync.sh              # Incremental sync (default offices)
#   ./sync.sh --full       # Full sync (default offices)
#   ./sync.sh --test       # Test sync (5 CVer)
#   ./sync.sh --all        # Sync ALL offices
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CV-RAG Synkronisering                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Run setup.sh first.${NC}"
    exit 1
fi

source venv/bin/activate

# Determine sync mode
SYNC_MODE="incremental"
ALL_OFFICES=""

if [ "$1" == "--full" ]; then
    SYNC_MODE="full"
    echo -e "${BLUE}📥 Mode: Full sync (default offices)${NC}"
elif [ "$1" == "--test" ]; then
    SYNC_MODE="test"
    echo -e "${BLUE}🧪 Mode: Test sync (5 CVer)${NC}"
elif [ "$1" == "--all" ]; then
    SYNC_MODE="full"
    ALL_OFFICES="--all-offices"
    echo -e "${BLUE}📥 Mode: Full sync (ALLE avdelinger)${NC}"
else
    SYNC_MODE="incremental"
    echo -e "${BLUE}📥 Mode: Incremental sync (sjekker hver CV individuelt)${NC}"
fi

if [ -z "$ALL_OFFICES" ]; then
    echo -e "${BLUE}🏢 Offices: Teknologi, Design, Trondheim, Management Consulting, Oppdrag${NC}"
else
    echo -e "${BLUE}🏢 Offices: ALLE${NC}"
fi
echo ""

# Run sync
echo -e "${GREEN}→ Synkroniserer med Flowcase...${NC}"
python scripts/sync_flowcase.py --auto --mode "$SYNC_MODE" $ALL_OFFICES

# Re-index
echo ""
echo -e "${GREEN}→ Re-indekserer CVer...${NC}"
echo "yes" | python scripts/reindex.py | tail -20

echo ""
echo -e "${GREEN}✅ Synkronisering fullført!${NC}"
echo ""
echo -e "${BLUE}Bruk:${NC}"
echo "  ./sync.sh              - Incremental sync (standard offices)"
echo "  ./sync.sh --full       - Full sync (standard offices)"
echo "  ./sync.sh --all        - Full sync (ALLE avdelinger)"
echo "  ./sync.sh --test       - Test med 5 CVer"
echo ""

