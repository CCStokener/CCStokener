package hr.fer.zemris.java.tecaj_5.vjezba.zadatak_2;

import java.util.Comparator;
public class Ekstremi<T extends Comparable<T>> {
	private T prvi;
	private T drugi;
	private Comparator<T> komparator;

	/**
	 * Konstruktor koji prima samo dve instance klase T. Za usporedbu se koristi 
	 * prirodni poredak.
	 * @param a prvi broj
	 * @param b drugi broj
	 */
	public Ekstremi(T a, T b) {
		super();
		prvi = a; 
		drugi = b;
		popraviRedosljed();
	}

	/**
	 * Konstruktor koji prima dve instance klase T i komparator koji se koristi 
	 * za usporedbu.
	 * @param a prvi broj
	 * @param b drugi broj
	 * @param komparator komparator koji treba koristiti za usporedbu
	 */
	public Ekstremi(T a, T b, Comparator<T> komparator) {
		super();
		prvi = a; 
		drugi = b;
		this.komparator = komparator;
		popraviRedosljed();
	}

	/**
	 * Metoda koja osigurava da element <tt>prvi</tt> uvijek bude manji 
	 * (ili jednak) od dva pohranjena elementa.
	 */
	private void popraviRedosljed() {
		int poredak = usporedi(prvi, drugi);
		if(poredak>0) {
			T pomocni = prvi;
			prvi = drugi;
			drugi = pomocni;
		}
	}
	/**
	 * Pomocna metoda koja sluzi za usporedbu dva elementa. Ako je zadan
	 * komparator, tada se on koristi. Inace se koristi prirodni poredak.
	 * @param x prvi broj
	 * @param y drugi broj
	 * @return rezultat usporedbe prvog broja s drugim.
	 */
	private int usporedi(T x, T y) {
		if(komparator!=null) {
			return komparator.compare(x, y);
		} else {
			return x.compareTo(y);
		}
	}
	/**
	 * Vraca manju od dvije pohranjene vrijednosti.
	 * @return manju vrijednost
	 */
	public T getMin() {
		return prvi;
	}
	/**
	 * Vraca vecu od dvije pohranjene vrijednosti.
	 * @return veca vrijednost
	 */
	public T getMax() {
		return drugi;
	}
	/**
	 * Metoda provjerava je li predani broj u intervalu koji je omeðen
	 * zadanim minimumom i maksimumom.
	 * @param arg broj koji se provjerava
	 * @return true ako je broj u intervalu, inace false 
	 */
	public boolean isInRange(T arg) {
		return usporedi(arg,prvi)>=0 && usporedi(arg,drugi)<=0;
	}
}