// Board.java
public class Board {
    private final char[][] grid;
    private static final int SIZE = 3;

    public Board() {
        grid = new char[SIZE][SIZE];
        reset();
    }

    public void reset() {
        for (int r = 0; r < SIZE; r++) {
            for (int c = 0; c < SIZE; c++) {
                grid[r][c] = ' ';
            }
        }
    }

    public boolean isValidCoordinate(int row, int col) {
        return row >= 0 && row < SIZE && col >= 0 && col < SIZE;
    }

    public boolean isCellEmpty(int row, int col) {
        if (!isValidCoordinate(row, col)) return false;
        return grid[row][col] == ' ';
    }

    public boolean makeMove(int row, int col, char symbol) {
        if (!isCellEmpty(row, col)) return false;
        grid[row][col] = symbol;
        return true;
    }

    public char checkWinner() {
        // Rows
        for (int r = 0; r < SIZE; r++) {
            if (grid[r][0] != ' ' && grid[r][0] == grid[r][1] && grid[r][1] == grid[r][2]) {
                return grid[r][0];
            }
        }
        // Columns
        for (int c = 0; c < SIZE; c++) {
            if (grid[0][c] != ' ' && grid[0][c] == grid[1][c] && grid[1][c] == grid[2][c]) {
                return grid[0][c];
            }
        }
        // Diagonals
        if (grid[0][0] != ' ' && grid[0][0] == grid[1][1] && grid[1][1] == grid[2][2]) {
            return grid[0][0];
        }
        if (grid[0][2] != ' ' && grid[0][2] == grid[1][1] && grid[1][1] == grid[2][0]) {
            return grid[0][2];
        }
        return ' ';
    }

    public boolean isFull() {
        for (int r = 0; r < SIZE; r++) {
            for (int c = 0; c < SIZE; c++) {
                if (grid[r][c] == ' ') return false;
            }
        }
        return true;
    }

    public void display() {
        System.out.println("  0   1   2");
        for (int r = 0; r < SIZE; r++) {
            System.out.printf("%d %c | %c | %c%n", r, grid[r][0], grid[r][1], grid[r][2]);
            if (r < SIZE - 1) {
                System.out.println("  ---------");
            }
        }
    }
}
