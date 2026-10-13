// TicTacToe.java
import java.util.Scanner;

public class TicTacToe {
    private final Board board;
    private final Player playerX;
    private final Player playerO;
    private Player currentPlayer;

    public TicTacToe() {
        board = new Board();
        playerX = new Player("Player X", 'X');
        playerO = new Player("Player O", 'O');
        currentPlayer = playerX;
    }

    public void switchPlayer() {
        currentPlayer = (currentPlayer == playerX) ? playerO : playerX;
    }

    public void start() {
        Scanner scanner = new Scanner(System.in);
        boolean playAgain = true;

        System.out.println("=== Welcome to Java Tic-Tac-Toe (ChatCollab Benchmark) ===");

        while (playAgain) {
            board.reset();
            currentPlayer = playerX;
            boolean gameOver = false;

            while (!gameOver) {
                System.out.println();
                board.display();
                System.out.printf("%s (%c)'s turn.%n", currentPlayer.getName(), currentPlayer.getSymbol());
                System.out.print("Enter row (0-2) and column (0-2) separated by space: ");

                if (!scanner.hasNextInt()) {
                    System.out.println("Invalid input! Please enter integers.");
                    scanner.nextLine();
                    continue;
                }
                int row = scanner.nextInt();

                if (!scanner.hasNextInt()) {
                    System.out.println("Invalid input! Please enter column integer.");
                    scanner.nextLine();
                    continue;
                }
                int col = scanner.nextInt();
                scanner.nextLine();

                if (!board.isValidCoordinate(row, col)) {
                    System.out.println("Error: Coordinates must be between 0 and 2!");
                    continue;
                }

                if (!board.makeMove(row, col, currentPlayer.getSymbol())) {
                    System.out.println("Error: That cell is already occupied. Choose another.");
                    continue;
                }

                char winner = board.checkWinner();
                if (winner != ' ') {
                    board.display();
                    System.out.printf("Congratulations! %s won the game!%n", currentPlayer.getName());
                    gameOver = true;
                } else if (board.isFull()) {
                    board.display();
                    System.out.println("It's a draw! Board is full.");
                    gameOver = true;
                } else {
                    switchPlayer();
                }
            }

            System.out.print("Play again? (y/n): ");
            String ans = scanner.nextLine().trim().toLowerCase();
            playAgain = ans.startsWith("y");
        }

        System.out.println("Thanks for playing!");
    }

    public static void main(String[] args) {
        new TicTacToe().start();
    }
}
