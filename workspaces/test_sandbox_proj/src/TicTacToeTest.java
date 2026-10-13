// TicTacToeTest.java
public class TicTacToeTest {
    private static int passed = 0;
    private static int failed = 0;

    private static void assertTrue(String testName, boolean condition) {
        if (condition) {
            System.out.println("[PASS] " + testName);
            passed++;
        } else {
            System.err.println("[FAIL] " + testName);
            failed++;
        }
    }

    public static void testInitialBoardEmpty() {
        Board b = new Board();
        assertTrue("Initial board is empty (cell 0,0)", b.isCellEmpty(0, 0));
        assertTrue("Initial board has no winner", b.checkWinner() == ' ');
        assertTrue("Initial board is not full", !b.isFull());
    }

    public static void testValidMove() {
        Board b = new Board();
        boolean moved = b.makeMove(1, 1, 'X');
        assertTrue("Move at (1,1) succeeds", moved);
        assertTrue("Cell (1,1) is no longer empty", !b.isCellEmpty(1, 1));
    }

    public static void testOccupiedCellRejected() {
        Board b = new Board();
        b.makeMove(0, 0, 'X');
        boolean movedAgain = b.makeMove(0, 0, 'O');
        assertTrue("Cannot overwrite occupied cell", !movedAgain);
    }

    public static void testHorizontalWin() {
        Board b = new Board();
        b.makeMove(0, 0, 'X');
        b.makeMove(0, 1, 'X');
        b.makeMove(0, 2, 'X');
        assertTrue("Row 0 win detected for X", b.checkWinner() == 'X');
    }

    public static void testVerticalWin() {
        Board b = new Board();
        b.makeMove(0, 1, 'O');
        b.makeMove(1, 1, 'O');
        b.makeMove(2, 1, 'O');
        assertTrue("Column 1 win detected for O", b.checkWinner() == 'O');
    }

    public static void testDiagonalWin() {
        Board b = new Board();
        b.makeMove(0, 0, 'X');
        b.makeMove(1, 1, 'X');
        b.makeMove(2, 2, 'X');
        assertTrue("Main diagonal win detected for X", b.checkWinner() == 'X');
    }

    public static void testDrawCondition() {
        Board b = new Board();
        // X O X
        // X X O
        // O X O
        b.makeMove(0, 0, 'X'); b.makeMove(0, 1, 'O'); b.makeMove(0, 2, 'X');
        b.makeMove(1, 0, 'X'); b.makeMove(1, 1, 'X'); b.makeMove(1, 2, 'O');
        b.makeMove(2, 0, 'O'); b.makeMove(2, 1, 'X'); b.makeMove(2, 2, 'O');

        assertTrue("Board is full on draw", b.isFull());
        assertTrue("Draw has no winner", b.checkWinner() == ' ');
    }

    public static void main(String[] args) {
        System.out.println("Running TicTacToe Test Suite...");
        testInitialBoardEmpty();
        testValidMove();
        testOccupiedCellRejected();
        testHorizontalWin();
        testVerticalWin();
        testDiagonalWin();
        testDrawCondition();

        System.out.printf("Test Results: %d passed, %d failed.%n", passed, failed);
        if (failed > 0) {
            System.exit(1);
        }
    }
}
